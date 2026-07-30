import Foundation
import Darwin

// ═══════════════════════════════════════════════════════════════
//  ProcessManager — Native process enumeration and management
//  Uses libproc for RSS, proc_listallpids for enumeration
// ═══════════════════════════════════════════════════════════════

struct ProcInfo {
    let pid: pid_t
    let ppid: pid_t
    let name: String
    let command: String
    let rssMB: Int
    let cpuPercent: Double
    let elapsedSeconds: Int
    let user: String
}

struct AppGroup {
    let label: String
    let pattern: String
    var processes: [ProcInfo] = []
    var totalRSSMB: Int { processes.reduce(0) { $0 + $1.rssMB } }
    var count: Int { processes.count }
}

final class ProcessManager {
    let config: Config
    let logger: Logger
    private let myUID = getuid()
    private var whitelist: [String] = []
    var killCount = 0

    init(config: Config, logger: Logger) {
        self.config = config
        self.logger = logger
        loadWhitelist()
    }

    func loadWhitelist() {
        let path = NSString(string: config.whitelistFile).expandingTildeInPath
        guard let content = try? String(contentsOfFile: path, encoding: .utf8) else { return }
        whitelist = content.components(separatedBy: .newlines)
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty && !$0.hasPrefix("#") }
    }

    // MARK: - Process enumeration via ps (reliable cross-version)

    func listProcesses() -> [ProcInfo] {
        let pipe = Pipe()
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/bin/ps")
        proc.arguments = ["aux", "-m"]
        proc.standardOutput = pipe
        proc.standardError = FileHandle.nullDevice

        do { try proc.run() } catch { return [] }
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        proc.waitUntilExit()
        guard let output = String(data: data, encoding: .utf8) else { return [] }

        var results: [ProcInfo] = []
        let lines = output.components(separatedBy: .newlines)

        for line in lines.dropFirst() {
            let cols = line.split(separator: " ", maxSplits: 10, omittingEmptySubsequences: true)
            guard cols.count >= 11 else { continue }

            let user = String(cols[0])
            guard let pid = pid_t(cols[1]) else { continue }
            let cpu = Double(cols[2]) ?? 0
            let rssKB = Int(cols[5]) ?? 0
            let command = String(cols[10...].joined(separator: " "))
            let name = URL(fileURLWithPath: String(cols[10])).lastPathComponent

            // Get PPID
            var kinfo = kinfo_proc()
            var size = MemoryLayout<kinfo_proc>.size
            var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, Int32(pid)]
            sysctl(&mib, 4, &kinfo, &size, nil, 0)
            let ppid = kinfo.kp_eproc.e_ppid

            // Get elapsed time
            let startSec = kinfo.kp_proc.p_starttime.tv_sec
            let elapsed = startSec > 0 ? Int(time(nil)) - startSec : 0

            results.append(ProcInfo(
                pid: pid, ppid: ppid, name: name, command: command,
                rssMB: rssKB / 1024, cpuPercent: cpu,
                elapsedSeconds: elapsed, user: user
            ))
        }
        return results
    }

    func appGroups(from procs: [ProcInfo]) -> [AppGroup] {
        var groups: [AppGroup] = [
            AppGroup(label: "Comet", pattern: "Comet"),
            AppGroup(label: "Node", pattern: "node"),
            AppGroup(label: "Renderer", pattern: "Helper (Renderer)"),
            AppGroup(label: "Python", pattern: "ython"),  // matches Python/python
        ]

        for proc in procs {
            for i in groups.indices {
                if proc.command.contains(groups[i].pattern) {
                    groups[i].processes.append(proc)
                    break
                }
            }
        }
        return groups
    }

    // MARK: - Kill with safety

    func ancestry(of proc: ProcInfo, allProcs: [ProcInfo], depth: Int = 3) -> String {
        var chain = "\(proc.pid)(\(proc.name))"
        var currentPPID = proc.ppid
        for _ in 0..<depth {
            guard currentPPID > 1,
                  let parent = allProcs.first(where: { $0.pid == currentPPID }) else { break }
            chain += "←\(parent.pid)(\(parent.name))"
            currentPPID = parent.ppid
        }
        return chain
    }

    func safeKill(_ proc: ProcInfo, reason: String, allProcs: [ProcInfo]) -> Bool {
        // Check whitelist
        for pattern in whitelist {
            if proc.command.contains(pattern) {
                logger.log(.skip, "PID=\(proc.pid) whitelisted: \(pattern)")
                return false
            }
        }

        // Only kill our own processes
        guard proc.user == NSUserName() else { return false }

        // Kill
        guard kill(proc.pid, SIGKILL) == 0 else { return false }

        let chain = ancestry(of: proc, allProcs: allProcs)
        logger.log(.kill, "PID=\(proc.pid) RSS=\(proc.rssMB)MB reason=\(reason) ancestry=[\(chain)]")
        killCount += 1
        return true
    }

    // MARK: - Strategies

    func cullExcess(group: inout AppGroup, maxCount: Int, allProcs: [ProcInfo]) {
        guard group.count > maxCount else { return }
        let excess = group.count - maxCount
        logger.log(.cull, "\(group.label): \(group.count) > max \(maxCount), culling \(excess)")

        // Kill oldest first (lowest PID)
        let sorted = group.processes.sorted { $0.pid < $1.pid }
        for proc in sorted.prefix(excess) {
            _ = safeKill(proc, reason: "cull-\(group.label)", allProcs: allProcs)
        }
    }

    func enforceBudget(group: inout AppGroup, budgetMB: Int, allProcs: [ProcInfo]) {
        guard budgetMB > 0, group.totalRSSMB > budgetMB else { return }
        logger.log(.budget, "\(group.label): \(group.totalRSSMB)MB > budget \(budgetMB)MB")

        // Kill largest RSS first
        var remaining = group.totalRSSMB
        let sorted = group.processes.sorted { $0.rssMB > $1.rssMB }
        for proc in sorted {
            guard remaining > budgetMB else { break }
            if safeKill(proc, reason: "budget-\(group.label)-\(proc.rssMB)MB", allProcs: allProcs) {
                remaining -= proc.rssMB
            }
        }
    }

    func killHot(group: AppGroup, cpuThreshold: Double, allProcs: [ProcInfo]) {
        for proc in group.processes where proc.cpuPercent >= cpuThreshold {
            _ = safeKill(proc, reason: "\(group.label)-cpu-\(Int(proc.cpuPercent))%", allProcs: allProcs)
        }
    }

    func killStaleRenderers(allProcs: [ProcInfo]) {
        let threshold = config.staleRendererMin * 60
        for proc in allProcs {
            guard proc.command.contains("Helper (Renderer)"),
                  proc.elapsedSeconds >= threshold,
                  proc.cpuPercent < 5.0 else { continue }
            _ = safeKill(proc, reason: "stale-renderer-\(proc.elapsedSeconds/60)min", allProcs: allProcs)
        }
    }

    func killCometDebug(allProcs: [ProcInfo]) {
        for proc in allProcs {
            guard proc.command.contains("Comet"),
                  proc.command.contains("--remote-debugging-port") else { continue }
            _ = safeKill(proc, reason: "comet-debug", allProcs: allProcs)
        }
    }

    func purge() {
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/sbin/purge")
        try? proc.run()
        proc.waitUntilExit()
        logger.log(.purge, "disk cache flushed")
    }

    func spotlightThrottle(_ enabled: Bool) {
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/mdutil")
        proc.arguments = ["-i", enabled ? "on" : "off", "/"]
        proc.standardOutput = FileHandle.nullDevice
        proc.standardError = FileHandle.nullDevice
        try? proc.run()
        proc.waitUntilExit()
        logger.log(.system, "Spotlight \(enabled ? "restored" : "paused")")
    }
}
