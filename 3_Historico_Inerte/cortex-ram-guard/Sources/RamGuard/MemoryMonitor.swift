import Foundation
import Darwin

// ═══════════════════════════════════════════════════════════════
//  MemoryMonitor — Native macOS memory pressure via Mach VM APIs
// ═══════════════════════════════════════════════════════════════

struct MemorySnapshot {
    let totalRAM: UInt64        // bytes
    let freePages: UInt64
    let activePages: UInt64
    let inactivePages: UInt64
    let wiredPages: UInt64
    let compressedPages: UInt64
    let pageSize: UInt64
    let swapUsedMB: Int
    let swapFreeMB: Int
    let timestamp: Date

    var totalRAMGB: Int { Int(totalRAM / (1024 * 1024 * 1024)) }
    var freeMB: Int { Int(freePages * pageSize / (1024 * 1024)) }
    var activeMB: Int { Int(activePages * pageSize / (1024 * 1024)) }
    var inactiveMB: Int { Int(inactivePages * pageSize / (1024 * 1024)) }
    var wiredMB: Int { Int(wiredPages * pageSize / (1024 * 1024)) }
    var compressedMB: Int { Int(compressedPages * pageSize / (1024 * 1024)) }
}

enum PressureLevel: String, Comparable {
    case green = "GREEN"
    case yellow = "YELLOW"
    case orange = "ORANGE"
    case red = "RED"

    var icon: String {
        switch self {
        case .green: return "🟢"
        case .yellow: return "🟡"
        case .orange: return "🟠"
        case .red: return "🔴"
        }
    }

    static func < (lhs: PressureLevel, rhs: PressureLevel) -> Bool {
        let order: [PressureLevel] = [.green, .yellow, .orange, .red]
        return order.firstIndex(of: lhs)! < order.firstIndex(of: rhs)!
    }
}

final class MemoryMonitor {
    private var config: Config
    private let totalRAM: UInt64

    init(config: Config) {
        self.config = config
        var size: size_t = MemoryLayout<UInt64>.size
        var ram: UInt64 = 0
        sysctlbyname("hw.memsize", &ram, &size, nil, 0)
        self.totalRAM = ram
    }

    func updateConfig(_ newConfig: Config) {
        self.config = newConfig
    }

    var totalRAMGB: Int { Int(totalRAM / (1024 * 1024 * 1024)) }

    var yellowThreshold: Int { totalRAMGB * config.yellowMult }
    var orangeThreshold: Int { totalRAMGB * config.orangeMult }
    var redThreshold: Int { totalRAMGB * config.redMult }

    func snapshot() -> MemorySnapshot {
        // Get VM statistics via Mach
        var stats = vm_statistics64()
        var count = mach_msg_type_number_t(MemoryLayout<vm_statistics64>.size / MemoryLayout<integer_t>.size)
        let host = mach_host_self()

        _ = withUnsafeMutablePointer(to: &stats) { ptr in
            ptr.withMemoryRebound(to: integer_t.self, capacity: Int(count)) { intPtr in
                host_statistics64(host, HOST_VM_INFO64, intPtr, &count)
            }
        }

        let pageSize = UInt64(vm_kernel_page_size)

        // Get swap via sysctl
        let (swapUsed, swapFree) = getSwapInfo()

        return MemorySnapshot(
            totalRAM: totalRAM,
            freePages: UInt64(stats.free_count),
            activePages: UInt64(stats.active_count),
            inactivePages: UInt64(stats.inactive_count),
            wiredPages: UInt64(stats.wire_count),
            compressedPages: UInt64(stats.compressor_page_count),
            pageSize: pageSize,
            swapUsedMB: swapUsed,
            swapFreeMB: swapFree,
            timestamp: Date()
        )
    }

    func pressureLevel(swapMB: Int) -> PressureLevel {
        if swapMB >= redThreshold { return .red }
        if swapMB >= orangeThreshold { return .orange }
        if swapMB >= yellowThreshold { return .yellow }
        return .green
    }

    // MARK: - Private

    private func getSwapInfo() -> (used: Int, free: Int) {
        var xswUsage = xsw_usage()
        var size = MemoryLayout<xsw_usage>.size
        sysctlbyname("vm.swapusage", &xswUsage, &size, nil, 0)
        let usedMB = Int(xswUsage.xsu_used / (1024 * 1024))
        let freeMB = Int(xswUsage.xsu_avail / (1024 * 1024))
        return (usedMB, freeMB)
    }
}
