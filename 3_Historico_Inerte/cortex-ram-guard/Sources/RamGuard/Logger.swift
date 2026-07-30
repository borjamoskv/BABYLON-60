import Foundation

// ═══════════════════════════════════════════════════════════════
//  Logger — Structured logging + daily rotation
// ═══════════════════════════════════════════════════════════════

enum LogLevel: String {
    case start = "START"
    case level = "LEVEL"
    case kill = "KILL"
    case skip = "SKIP"
    case cull = "CULL"
    case budget = "BUDGET"
    case purge = "PURGE"
    case system = "SYSTEM"
    case predict = "PREDICT"
    case leak = "LEAK"
    case selfHealth = "SELF"
    case cooldown = "COOLDOWN"
    case info = "INFO"
    case manual = "MANUAL"
}

final class Logger {
    private let logDir: String
    private var currentDate: String
    private var fileHandle: FileHandle?
    private let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd'T'HH:mm:ssZ"
        return f
    }()

    init() {
        self.logDir = Config.guardDir + "/logs"
        self.currentDate = Logger.today()
        openLogFile()
    }

    deinit { fileHandle?.closeFile() }

    func log(_ level: LogLevel, _ message: String) {
        let today = Logger.today()
        if today != currentDate {
            currentDate = today
            openLogFile()
        }
        let line = "[\(dateFormatter.string(from: Date()))] [\(level.rawValue)] \(message)\n"
        if let data = line.data(using: .utf8) {
            fileHandle?.write(data)
            try? fileHandle?.synchronize()
        }
    }

    func rotate(compressDays: Int, deleteDays: Int) {
        let fm = FileManager.default
        guard let files = try? fm.contentsOfDirectory(atPath: logDir) else { return }

        for file in files {
            let path = logDir + "/" + file
            guard let attrs = try? fm.attributesOfItem(atPath: path),
                  let modDate = attrs[.modificationDate] as? Date else { continue }

            let age = -modDate.timeIntervalSinceNow / 86400

            if file.hasSuffix(".log.gz") && age > Double(deleteDays) {
                try? fm.removeItem(atPath: path)
            } else if file.hasSuffix(".log") && !file.contains(currentDate) && age > Double(compressDays) {
                let task = Process()
                task.executableURL = URL(fileURLWithPath: "/usr/bin/gzip")
                task.arguments = ["-q", path]
                try? task.run()
                task.waitUntilExit()
            }
        }
    }

    // MARK: - Private

    private func openLogFile() {
        fileHandle?.closeFile()
        let path = logDir + "/ram-guard-\(currentDate).log"
        if !FileManager.default.fileExists(atPath: path) {
            FileManager.default.createFile(atPath: path, contents: nil)
        }
        fileHandle = FileHandle(forWritingAtPath: path)
        fileHandle?.seekToEndOfFile()
    }

    private static func today() -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f.string(from: Date())
    }
}
