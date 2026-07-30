import Foundation

// ═══════════════════════════════════════════════════════════════
//  Config — Parsed from ~/.cortex/ram-guard/config.conf
// ═══════════════════════════════════════════════════════════════

struct Config {
    var yellowMult = 500
    var orangeMult = 800
    var redMult = 1200

    var maxCometProcs = 20
    var maxNodeProcs = 80
    var maxRendererProcs = 12

    var cpuKillPython: Double = 60
    var cpuKillNode: Double = 70
    var cpuKillRenderer: Double = 50

    var budgetCometMB = 1500
    var budgetNodeMB = 2000
    var budgetRendererMB = 1800
    var budgetPythonMB = 1200

    var intervalGreen: TimeInterval = 120
    var intervalYellow: TimeInterval = 60
    var intervalOrange: TimeInterval = 30
    var intervalRed: TimeInterval = 15
    var cooldownSeconds: TimeInterval = 180

    func interval(for level: PressureLevel) -> TimeInterval {
        switch level {
        case .green: return intervalGreen
        case .yellow: return intervalYellow
        case .orange: return intervalOrange
        case .red: return intervalRed
        }
    }

    var trendWindow = 10
    var trendToleranceMB = 100
    var staleRendererMin = 90
    var predictAlertMin = 15
    var selfMaxRSSMB = 50

    var logCompressDays = 3
    var logDeleteDays = 14
    var notifyEnabled = true
    var notifyBatchSeconds: TimeInterval = 120

    var whitelistFile = "~/.cortex/ram-guard/whitelist.conf"

    static let guardDir: String = {
        let dir = NSHomeDirectory() + "/.cortex/ram-guard"
        try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
        try? FileManager.default.createDirectory(atPath: dir + "/logs", withIntermediateDirectories: true)
        try? FileManager.default.createDirectory(atPath: dir + "/snapshots", withIntermediateDirectories: true)
        return dir
    }()

    static func load() -> Config {
        var config = Config()
        let path = guardDir + "/config.conf"

        guard let content = try? String(contentsOfFile: path, encoding: .utf8) else {
            return config
        }

        for line in content.components(separatedBy: .newlines) {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            guard !trimmed.isEmpty, !trimmed.hasPrefix("#") else { continue }

            let parts = trimmed.split(separator: "=", maxSplits: 1)
            guard parts.count == 2 else { continue }

            let key = parts[0].trimmingCharacters(in: .whitespaces)
            let val = parts[1].trimmingCharacters(in: .whitespaces)
                .components(separatedBy: "#").first?
                .trimmingCharacters(in: .whitespaces) ?? ""

            switch key {
            case "YELLOW_MULT": config.yellowMult = Int(val) ?? config.yellowMult
            case "ORANGE_MULT": config.orangeMult = Int(val) ?? config.orangeMult
            case "RED_MULT": config.redMult = Int(val) ?? config.redMult
            case "MAX_COMET_PROCS": config.maxCometProcs = Int(val) ?? config.maxCometProcs
            case "MAX_NODE_PROCS": config.maxNodeProcs = Int(val) ?? config.maxNodeProcs
            case "MAX_RENDERER_PROCS": config.maxRendererProcs = Int(val) ?? config.maxRendererProcs
            case "CPU_KILL_PYTHON": config.cpuKillPython = Double(val) ?? config.cpuKillPython
            case "CPU_KILL_NODE": config.cpuKillNode = Double(val) ?? config.cpuKillNode
            case "CPU_KILL_RENDERER": config.cpuKillRenderer = Double(val) ?? config.cpuKillRenderer
            case "BUDGET_COMET_MB": config.budgetCometMB = Int(val) ?? config.budgetCometMB
            case "BUDGET_NODE_MB": config.budgetNodeMB = Int(val) ?? config.budgetNodeMB
            case "BUDGET_RENDERER_MB": config.budgetRendererMB = Int(val) ?? config.budgetRendererMB
            case "BUDGET_PYTHON_MB": config.budgetPythonMB = Int(val) ?? config.budgetPythonMB
            case "INTERVAL_GREEN": config.intervalGreen = Double(val) ?? config.intervalGreen
            case "INTERVAL_YELLOW": config.intervalYellow = Double(val) ?? config.intervalYellow
            case "INTERVAL_ORANGE": config.intervalOrange = Double(val) ?? config.intervalOrange
            case "INTERVAL_RED": config.intervalRed = Double(val) ?? config.intervalRed
            case "COOLDOWN_SECONDS": config.cooldownSeconds = Double(val) ?? config.cooldownSeconds
            case "TREND_WINDOW": config.trendWindow = Int(val) ?? config.trendWindow
            case "TREND_TOLERANCE_MB": config.trendToleranceMB = Int(val) ?? config.trendToleranceMB
            case "STALE_RENDERER_MIN": config.staleRendererMin = Int(val) ?? config.staleRendererMin
            case "PREDICT_ALERT_MIN": config.predictAlertMin = Int(val) ?? config.predictAlertMin
            case "SELF_MAX_RSS_MB": config.selfMaxRSSMB = Int(val) ?? config.selfMaxRSSMB
            case "NOTIFY_ENABLED": config.notifyEnabled = val == "1"
            case "WHITELIST_FILE": config.whitelistFile = val
            default: break
            }
        }
        return config
    }
}
