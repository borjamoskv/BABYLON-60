import ArgumentParser
import Foundation

// ═══════════════════════════════════════════════════════════════
//  ramguard — CLI entry point
// ═══════════════════════════════════════════════════════════════

@main
struct RamGuard: ParsableCommand {
    static let configuration = CommandConfiguration(
        commandName: "ramguard",
        abstract: "Sovereign macOS memory pressure daemon",
        version: "3.0.0",
        subcommands: [Run.self, Status.self, Purge.self, Logs.self, Stats.self, Install.self, Uninstall.self],
        defaultSubcommand: Run.self
    )
}

// MARK: - Daemon

struct Run: ParsableCommand {
    static let configuration = CommandConfiguration(abstract: "Run the daemon (default)")
    func run() { Daemon().run() }
}

// MARK: - Status

struct Status: ParsableCommand {
    static let configuration = CommandConfiguration(abstract: "Show current memory state")

    func run() {
        let config = Config.load()
        let monitor = MemoryMonitor(config: config)
        let snap = monitor.snapshot()
        let level = monitor.pressureLevel(swapMB: snap.swapUsedMB)
        let procMgr = ProcessManager(config: config, logger: Logger())
        let allProcs = procMgr.listProcesses()
        let groups = procMgr.appGroups(from: allProcs)

        print("═══════════════════════════════════════════════")
        print("  CORTEX RAM GUARD v3.0 (Swift)")
        print("═══════════════════════════════════════════════")
        print("  RAM:       \(monitor.totalRAMGB)GB  │  Free: \(snap.freeMB)MB")
        print("  Swap:      \(snap.swapUsedMB)MB  │  \(level.icon) \(level.rawValue)")
        print("  Compressed:\(snap.compressedMB)MB  │  Wired: \(snap.wiredMB)MB")
        print("  Thresholds: Y=\(monitor.yellowThreshold) O=\(monitor.orangeThreshold) R=\(monitor.redThreshold)")
        print("───────────────────────────────────────────────")

        let budgets = ["Comet": config.budgetCometMB, "Node": config.budgetNodeMB,
                       "Renderer": config.budgetRendererMB, "Python": config.budgetPythonMB]
        for g in groups {
            let budget = budgets[g.label] ?? 0
            let bar = g.totalRSSMB > budget && budget > 0 ? " ⚠️" : ""
            let labelPad = g.label.padding(toLength: 12, withPad: " ", startingAt: 0)
            print(String(format: "  %@ %3d procs  %5dMB RSS  (budget %dMB)%@",
                         labelPad, g.count, g.totalRSSMB, budget, bar))
        }

        print("───────────────────────────────────────────────")
        print("  Total procs: \(allProcs.count)")

        // Load today's stats
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"
        let statsPath = Config.guardDir + "/stats-\(f.string(from: Date())).json"
        if let data = try? Data(contentsOf: URL(fileURLWithPath: statsPath)),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            let kills = json["kills"] as? Int ?? 0
            let purges = json["purges"] as? Int ?? 0
            let freed = json["freed_mb"] as? Int ?? 0
            print("  Today: kills=\(kills) purges=\(purges) freed=\(freed)MB")
        }
        print("═══════════════════════════════════════════════")
    }
}

// MARK: - Manual Purge

struct Purge: ParsableCommand {
    static let configuration = CommandConfiguration(abstract: "Manual immediate purge")

    func run() {
        print("⚡ Manual purge...")
        let config = Config.load()
        let monitor = MemoryMonitor(config: config)
        let logger = Logger()
        let procMgr = ProcessManager(config: config, logger: logger)

        let before = monitor.snapshot().swapUsedMB
        let allProcs = procMgr.listProcesses()
        var groups = procMgr.appGroups(from: allProcs)

        procMgr.killCometDebug(allProcs: allProcs)
        procMgr.killStaleRenderers(allProcs: allProcs)
        for i in groups.indices {
            let (max, budget): (Int, Int) = {
                switch groups[i].label {
                case "Comet": return (config.maxCometProcs, config.budgetCometMB)
                case "Node": return (config.maxNodeProcs, config.budgetNodeMB)
                case "Renderer": return (config.maxRendererProcs, config.budgetRendererMB)
                case "Python": return (999, config.budgetPythonMB)
                default: return (999, 0)
                }
            }()
            procMgr.cullExcess(group: &groups[i], maxCount: max, allProcs: allProcs)
            procMgr.enforceBudget(group: &groups[i], budgetMB: budget, allProcs: allProcs)
        }
        procMgr.purge()

        Thread.sleep(forTimeInterval: 3)
        let after = monitor.snapshot().swapUsedMB
        print("✓ Swap: \(before)MB → \(after)MB (freed \(before - after)MB)")
        logger.log(.manual, "purge freed=\(before - after)MB kills=\(procMgr.killCount)")
    }
}

// MARK: - Logs

struct Logs: ParsableCommand {
    static let configuration = CommandConfiguration(abstract: "Tail today's log")

    func run() {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"
        let path = Config.guardDir + "/logs/ram-guard-\(f.string(from: Date())).log"
        guard let content = try? String(contentsOfFile: path, encoding: .utf8) else {
            print("No logs today."); return
        }
        let lines = content.components(separatedBy: .newlines)
        for line in lines.suffix(50) { print(line) }
    }
}

// MARK: - Stats

struct Stats: ParsableCommand {
    static let configuration = CommandConfiguration(abstract: "7-day history")

    func run() {
        print("═══════════════════════════════════════════════")
        print("  CORTEX RAM GUARD — 7-DAY HISTORY")
        print("═══════════════════════════════════════════════")
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"
        for i in 0..<7 {
            let date = Calendar.current.date(byAdding: .day, value: -i, to: Date())!
            let day = f.string(from: date)
            let path = Config.guardDir + "/stats-\(day).json"
            guard let data = try? Data(contentsOf: URL(fileURLWithPath: path)),
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { continue }
            let k = json["kills"] as? Int ?? 0
            let p = json["purges"] as? Int ?? 0
            let freed = json["freed_mb"] as? Int ?? 0
            let lvl = json["last_level"] as? String ?? "?"
            print(String(format: "  %@  kills=%3d  purges=%2d  freed=%5dMB  level=%@", day, k, p, freed, lvl))
        }
        print("═══════════════════════════════════════════════")
    }
}

// MARK: - Install / Uninstall

struct Install: ParsableCommand {
    static let configuration = CommandConfiguration(abstract: "Install launchd daemon")

    func run() {
        let plistPath = NSHomeDirectory() + "/Library/LaunchAgents/com.cortex.ram-guard.plist"
        let execPath = CommandLine.arguments[0]

        // Unload if exists
        let _ = shell("/bin/launchctl", ["bootout", "gui/\(getuid())", plistPath])

        let plist = """
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0"><dict>
          <key>Label</key><string>com.cortex.ram-guard</string>
          <key>ProgramArguments</key><array><string>\(execPath)</string><string>run</string></array>
          <key>RunAtLoad</key><true/>
          <key>KeepAlive</key><true/>
          <key>StandardOutPath</key><string>\(Config.guardDir)/logs/stdout.log</string>
          <key>StandardErrorPath</key><string>\(Config.guardDir)/logs/stderr.log</string>
          <key>ThrottleInterval</key><integer>30</integer>
          <key>ProcessType</key><string>Background</string>
          <key>LowPriorityBackgroundIO</key><true/>
          <key>Nice</key><integer>10</integer>
        </dict></plist>
        """
        try! plist.write(toFile: plistPath, atomically: true, encoding: .utf8)
        let _ = shell("/bin/launchctl", ["bootstrap", "gui/\(getuid())", plistPath])
        print("✓ Installed & started")
    }

    private func shell(_ cmd: String, _ args: [String]) -> Int32 {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: cmd)
        p.arguments = args
        p.standardOutput = FileHandle.nullDevice
        p.standardError = FileHandle.nullDevice
        try? p.run()
        p.waitUntilExit()
        return p.terminationStatus
    }
}

struct Uninstall: ParsableCommand {
    static let configuration = CommandConfiguration(abstract: "Stop and unload daemon")

    func run() {
        let plistPath = NSHomeDirectory() + "/Library/LaunchAgents/com.cortex.ram-guard.plist"
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/bin/launchctl")
        p.arguments = ["bootout", "gui/\(getuid())", plistPath]
        p.standardOutput = FileHandle.nullDevice
        p.standardError = FileHandle.nullDevice
        try? p.run()
        p.waitUntilExit()
        print("✓ Daemon stopped & unloaded")
    }
}
