import Foundation

// ═══════════════════════════════════════════════════════════════
//  Daemon — Main loop with graduated response
// ═══════════════════════════════════════════════════════════════

final class Daemon {
    private var config: Config
    private let monitor: MemoryMonitor
    private var procMgr: ProcessManager
    private let logger: Logger
    private var swapHistory: [Int] = []
    private var spotlightThrottled = false
    private var lastCooldown: Date = .distantPast
    private var cycle = 0
    private var totalFreedMB = 0
    private var purgeCount = 0
    private var pendingNotifs: [String] = []
    private var lastNotify: Date = .distantPast

    init() {
        self.config = Config.load()
        self.logger = Logger()
        self.monitor = MemoryMonitor(config: config)
        self.procMgr = ProcessManager(config: config, logger: logger)
    }

    func run() -> Never {
        writePID()
        logger.log(.start, "v3.0-swift RAM=\(monitor.totalRAMGB)GB Y=\(monitor.yellowThreshold) O=\(monitor.orangeThreshold) R=\(monitor.redThreshold)")

        while true {

            let snap = monitor.snapshot()
            let level = monitor.pressureLevel(swapMB: snap.swapUsedMB)
            logger.log(.level, "\(level.rawValue) swap=\(snap.swapUsedMB)MB")
            updateTrend(snap.swapUsedMB)

            // Snapshot every 30 cycles
            if cycle % 30 == 0 { takeSnapshot() }

            let swapBefore = snap.swapUsedMB

            // Always enforce budgets and cull excess if configured
            enforceBudgets()

            switch level {
            case .green:
                if spotlightThrottled {
                    procMgr.spotlightThrottle(true)
                    spotlightThrottled = false
                }
            case .yellow:
                // Yellow specific actions (none currently, just budgeting which is now global)
                break
            case .orange:
                respondOrange(swapMB: snap.swapUsedMB)
            case .red:
                respondRed(swapMB: snap.swapUsedMB)
            }

            // Measure freed
            Thread.sleep(forTimeInterval: 2)
            let snapAfter = monitor.snapshot()
            let freed = swapBefore - snapAfter.swapUsedMB
            if freed > 0 { totalFreedMB += freed }

            // Predictive alert
            let eta = predictTimeToRed(level: level)
            if eta >= 0 && eta < config.predictAlertMin && level != .red {
                logger.log(.predict, "ETA to RED: \(eta)min")
                queueNotify("⏱ RED en ~\(eta)min")
            }

            // Leak detection
            if detectLeak() {
                logger.log(.leak, "Monotonic swap growth across \(config.trendWindow) samples")
                queueNotify("🔍 Memory leak detectado")
            }

            flushNotifications()
            checkSelfHealth()
            saveStats(level: level, swapMB: snapAfter.swapUsedMB)

            // Log rotation every 60 cycles
            if cycle % 60 == 0 {
                logger.rotate(compressDays: config.logCompressDays, deleteDays: config.logDeleteDays)
            }

            // Periodic config reload (every 10 cycles)
            if cycle % 10 == 0 {
                reloadConfig()
            }

            cycle += 1
            
            let sleepTime = config.interval(for: level)
            Thread.sleep(forTimeInterval: sleepTime)
        }
    }

    private func reloadConfig() {
        self.config = Config.load()
        self.procMgr.loadWhitelist()
        self.monitor.updateConfig(config)
    }

    // MARK: - Responses

    private func enforceBudgets() {
        let allProcs = procMgr.listProcesses()
        var groups = procMgr.appGroups(from: allProcs)

        for i in groups.indices {
            let maxCount: Int
            let budget: Int
            switch groups[i].label {
            case "Comet": maxCount = config.maxCometProcs; budget = config.budgetCometMB
            case "Node": maxCount = config.maxNodeProcs; budget = config.budgetNodeMB
            case "Renderer": maxCount = config.maxRendererProcs; budget = config.budgetRendererMB
            case "Python": maxCount = 999; budget = config.budgetPythonMB
            default: continue
            }
            if maxCount < 999 {
                procMgr.cullExcess(group: &groups[i], maxCount: maxCount, allProcs: allProcs)
            }
            if budget > 0 {
                procMgr.enforceBudget(group: &groups[i], budgetMB: budget, allProcs: allProcs)
            }
        }
    }

    private func respondYellow() {
        // Budgeting is now handled in enforceBudgets()
        procMgr.killStaleRenderers(allProcs: procMgr.listProcesses())
    }

    private func respondOrange(swapMB: Int) {
        logger.log(.level, "ORANGE swap=\(swapMB)MB")
        guard !isInCooldown() else {
            logger.log(.cooldown, "skip"); return
        }
        respondYellow()

        let allProcs = procMgr.listProcesses()
        let groups = procMgr.appGroups(from: allProcs)

        for g in groups {
            let thresh: Double
            switch g.label {
            case "Python": thresh = config.cpuKillPython
            case "Node": thresh = config.cpuKillNode
            case "Renderer": thresh = config.cpuKillRenderer
            default: continue
            }
            procMgr.killHot(group: g, cpuThreshold: thresh, allProcs: allProcs)
        }
        procMgr.killCometDebug(allProcs: allProcs)
        procMgr.purge()
        purgeCount += 1
        setCooldown()
        queueNotify("ORANGE — purge swap=\(swapMB)MB")
    }

    private func respondRed(swapMB: Int) {
        logger.log(.level, "RED swap=\(swapMB)MB")
        guard !isInCooldown() else {
            logger.log(.cooldown, "skip"); return
        }
        respondYellow()

        let allProcs = procMgr.listProcesses()
        procMgr.killHot(group: AppGroup(label: "Python", pattern: "ython", processes: allProcs.filter { $0.command.contains("ython") }),
                        cpuThreshold: 30, allProcs: allProcs)
        procMgr.killHot(group: AppGroup(label: "Node", pattern: "node", processes: allProcs.filter { $0.command.contains("node") }),
                        cpuThreshold: 40, allProcs: allProcs)
        procMgr.killCometDebug(allProcs: allProcs)

        // Kill old renderers (>30min in RED)
        for proc in allProcs where proc.command.contains("Helper (Renderer)") && proc.elapsedSeconds > 1800 {
            _ = procMgr.safeKill(proc, reason: "red-renderer-old", allProcs: allProcs)
        }

        procMgr.spotlightThrottle(false)
        spotlightThrottled = true
        procMgr.purge()
        purgeCount += 1
        setCooldown()
        queueNotify("⚠️ RED CRÍTICO — swap=\(swapMB)MB")
    }

    // MARK: - Trend & Prediction

    private func updateTrend(_ swapMB: Int) {
        swapHistory.append(swapMB)
        if swapHistory.count > config.trendWindow {
            swapHistory.removeFirst()
        }
    }

    private func detectLeak() -> Bool {
        guard swapHistory.count >= config.trendWindow else { return false }
        var increasing = 0
        for i in 1..<swapHistory.count {
            if swapHistory[i] > swapHistory[i-1] + config.trendToleranceMB {
                increasing += 1
            }
        }
        return increasing >= config.trendWindow * 80 / 100
    }

    private func predictTimeToRed(level: PressureLevel) -> Int {
        guard swapHistory.count >= 3 else { return -1 }
        let first = swapHistory.first!
        let last = swapHistory.last!
        let n = swapHistory.count
        let elapsedMin = Int(Double(n - 1) * config.interval(for: level) / 60)
        guard elapsedMin > 0 else { return -1 }
        let ratePerMin = (last - first) / elapsedMin
        guard ratePerMin > 0 else { return -1 }
        let remaining = monitor.redThreshold - last
        guard remaining > 0 else { return 0 }
        return remaining / ratePerMin
    }

    // MARK: - Utilities

    private func isInCooldown() -> Bool {
        -lastCooldown.timeIntervalSinceNow < config.cooldownSeconds
    }

    private func setCooldown() { lastCooldown = Date() }

    private func writePID() {
        let path = Config.guardDir + "/guard.pid"
        try? "\(Foundation.ProcessInfo.processInfo.processIdentifier)".write(toFile: path, atomically: true, encoding: .utf8)
    }

    private func checkSelfHealth() {
        var info = rusage()
        getrusage(RUSAGE_SELF, &info)
        let rssMB = info.ru_maxrss / (1024 * 1024)
        if rssMB > config.selfMaxRSSMB {
            logger.log(.selfHealth, "RSS=\(rssMB)MB > limit \(config.selfMaxRSSMB)MB")
        }
    }

    private func takeSnapshot() {
        let procs = procMgr.listProcesses().sorted { $0.rssMB > $1.rssMB }.prefix(30)
        let path = Config.guardDir + "/snapshots/snap-\(snapshotTimestamp()).tsv"
        var content = "PID\tRSS_MB\tCPU%\tELAPSED_S\tCOMMAND\n"
        for p in procs {
            content += "\(p.pid)\t\(p.rssMB)\t\(p.cpuPercent)\t\(p.elapsedSeconds)\t\(p.name)\n"
        }
        try? content.write(toFile: path, atomically: true, encoding: .utf8)

        // Keep only last 24
        let dir = Config.guardDir + "/snapshots"
        if let files = try? FileManager.default.contentsOfDirectory(atPath: dir).sorted().reversed() {
            for f in files.dropFirst(24) {
                try? FileManager.default.removeItem(atPath: dir + "/" + f)
            }
        }
    }

    private func snapshotTimestamp() -> String {
        let f = DateFormatter()
        f.dateFormat = "HHmm"
        return f.string(from: Date())
    }

    private func saveStats(level: PressureLevel, swapMB: Int) {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        let today = f.string(from: Date())
        let path = Config.guardDir + "/stats-\(today).json"
        let json = """
        {"date":"\(today)","kills":\(procMgr.killCount),"purges":\(purgeCount),\
        "freed_mb":\(totalFreedMB),"ram_gb":\(monitor.totalRAMGB),\
        "last_swap_mb":\(swapMB),"last_level":"\(level.rawValue)",\
        "updated":"\(ISO8601DateFormatter().string(from: Date()))"}
        """
        try? json.write(toFile: path, atomically: true, encoding: .utf8)
    }

    // MARK: - Notifications

    private func queueNotify(_ msg: String) { pendingNotifs.append(msg) }

    private func flushNotifications() {
        guard config.notifyEnabled,
              -lastNotify.timeIntervalSinceNow >= config.notifyBatchSeconds,
              !pendingNotifs.isEmpty else { return }

        let summary = "\(pendingNotifs.count) actions"
        let body = pendingNotifs.first! + (pendingNotifs.count > 1 ? " (+\(pendingNotifs.count - 1) more)" : "")
        let script = "display notification \"\(body)\" with title \"⚡ RAM Guard — \(summary)\""

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        proc.arguments = ["-e", script]
        proc.standardOutput = FileHandle.nullDevice
        proc.standardError = FileHandle.nullDevice
        try? proc.run()

        pendingNotifs.removeAll()
        lastNotify = Date()
    }
}
