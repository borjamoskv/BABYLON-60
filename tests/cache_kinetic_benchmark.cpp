/**
 * ============================================================================
 * BABYLON-60 : KINETIC ENGINE EMPIRICAL CACHE BENCHMARK
 * Target: aarch64-apple-darwin / x86_64-pc-linux-gnu
 * Axiomas: Aislamiento L1 Cache Line (False Sharing Mitigation)
 * ============================================================================
 * 
 * Este benchmark demuestra el efecto técnico patentable del TopologicalCompressor
 * y el secunciador Lock-Free, al medir la degradación masiva de throughput y
 * tail-latency generada por el "False Sharing" cuando se viola el axioma AX-CONC-01.
 */

#include <iostream>
#include <atomic>
#include <cstdint>
#include <thread>
#include <vector>
#include <chrono>
#include <algorithm>
#include <iomanip>
#include <string>

// Simulación del Payload
struct alignas(64) SharedManifest {
    uint32_t status_flag;
    uint32_t seq;
    uint64_t epoch_id;
    uint64_t payload_hash[4];
    uint8_t  _padding[16];
};

static_assert(sizeof(SharedManifest) == 64, "SharedManifest layout error");

#ifdef __cpp_lib_hardware_interference_size
    using std::hardware_destructive_interference_size;
#else
    constexpr std::size_t hardware_destructive_interference_size = 64;
#endif

// ============================================================================
// RING BUFFER TEMPLATE (Topological State Parameterized)
// ============================================================================

template <typename T, std::size_t Capacity, bool KineticIsolation>
class BenchmarkSequencerSPSC {
    static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be power of 2");

private:
    struct Slot { T storage; };
    Slot buffer_[Capacity];

    // Topological Isolation: Si KineticIsolation es true, se fuerza el aislamiento.
    // Si es false, se empaquetan contiguamente para forzar L1 False Sharing.

#pragma pack(push, 1)
    struct State {
        // En modo KINETIC aisla cabeza y cola. En modo DEGRADADO los comprime.
        alignas(KineticIsolation ? hardware_destructive_interference_size : 8) std::atomic<std::size_t> head{0};
        alignas(KineticIsolation ? hardware_destructive_interference_size : 8) std::atomic<std::size_t> tail{0};
    } state_;
#pragma pack(pop)

public:
    bool push(const T& item) noexcept {
        const auto current_head = state_.head.load(std::memory_order_relaxed);
        const auto current_tail = state_.tail.load(std::memory_order_acquire);
        if ((current_head - current_tail) >= Capacity) return false;
        
        buffer_[current_head & (Capacity - 1)].storage = item;
        state_.head.store(current_head + 1, std::memory_order_release);
        return true;
    }

    bool pop(T& item) noexcept {
        const auto current_tail = state_.tail.load(std::memory_order_relaxed);
        const auto current_head = state_.head.load(std::memory_order_acquire);
        if (current_tail == current_head) return false;

        item = buffer_[current_tail & (Capacity - 1)].storage;
        state_.tail.store(current_tail + 1, std::memory_order_release);
        return true;
    }
};

// ============================================================================
// HARNESS EXECUTION
// ============================================================================

template <bool KineticIsolation>
void RunBenchmark(const std::string& name, std::size_t total_operations) {
    constexpr std::size_t CAPACITY = 8192;
    constexpr std::size_t SAMPLE_INTERVAL = 1000;

    BenchmarkSequencerSPSC<SharedManifest, CAPACITY, KineticIsolation> ring_buffer;

    std::atomic<bool> start_flag{false};
    std::vector<uint64_t> latency_samples_ns;
    latency_samples_ns.reserve(total_operations / SAMPLE_INTERVAL);

    // Consumidor (Thread B)
    std::thread consumer([&]() {
        while (!start_flag.load(std::memory_order_acquire)) { std::this_thread::yield(); }

        std::size_t consumed = 0;
        SharedManifest manifest{};

        while (consumed < total_operations) {
            auto pop_start = std::chrono::high_resolution_clock::now();
            if (ring_buffer.pop(manifest)) {
                auto pop_end = std::chrono::high_resolution_clock::now();
                if (consumed % SAMPLE_INTERVAL == 0) {
                    uint64_t lat = std::chrono::duration_cast<std::chrono::nanoseconds>(pop_end - pop_start).count();
                    latency_samples_ns.push_back(lat);
                }
                consumed++;
            } else {
                // Pequeña espera activa para saturar el bus de memoria (L1 evictions)
            }
        }
    });

    // Productor (Thread A)
    std::thread producer([&]() {
        while (!start_flag.load(std::memory_order_acquire)) { std::this_thread::yield(); }

        for (std::size_t i = 1; i <= total_operations; ++i) {
            SharedManifest manifest{ .status_flag = 1, .seq = static_cast<uint32_t>(i), .epoch_id = i };
            while (!ring_buffer.push(manifest)) {} // Active wait
        }
    });

    // Sincronización Cuántica de Arranque
    auto start_time = std::chrono::high_resolution_clock::now();
    start_flag.store(true, std::memory_order_release);

    producer.join();
    consumer.join();
    auto end_time = std::chrono::high_resolution_clock::now();

    auto elapsed_us = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time).count();
    double elapsed_ms = elapsed_us / 1000.0;
    double ops_per_sec = (static_cast<double>(total_operations) / (elapsed_us > 0 ? elapsed_us : 1)) * 1'000'000.0;

    std::sort(latency_samples_ns.begin(), latency_samples_ns.end());
    uint64_t lat_p50 = latency_samples_ns[latency_samples_ns.size() * 0.50];
    uint64_t lat_p99 = latency_samples_ns[latency_samples_ns.size() * 0.99];
    uint64_t lat_p999 = latency_samples_ns[latency_samples_ns.size() * 0.999];
    uint64_t lat_max = latency_samples_ns.back();

    std::cout << "--- " << name << " ---\n";
    std::cout << "Throughput: " << std::fixed << std::setprecision(2) << (ops_per_sec / 1'000'000.0) << " Mops/sec\n";
    std::cout << "Latencia p50  : " << lat_p50 << " ns\n";
    std::cout << "Latencia p99  : " << lat_p99 << " ns\n";
    std::cout << "Latencia p99.9: " << lat_p999 << " ns\n";
    std::cout << "Latencia Max  : " << lat_max << " ns\n";
    std::cout << "Total Ops     : " << total_operations << "\n";
    std::cout << "Tiempo Total  : " << elapsed_ms << " ms\n\n";
}

int main(int argc, char** argv) {
    std::size_t total_ops = 10'000'000;
    if (argc > 1) {
        total_ops = std::stoull(argv[1]);
    }

    std::cout << "[KINETIC ENGINE] INICIANDO BENCHMARK DE TOPOLOGÍA (Xi-Exergy)\n\n";

    // 1. Variante Degradada (False Sharing activo)
    RunBenchmark<false>("MODO DEGRADADO (False Sharing L1 Cache)", total_ops);

    // 2. Variante Kinetic (Aislamiento Cache Line)
    RunBenchmark<true>("MODO KINETIC (AX-CONC-01 Aislamiento)", total_ops);

    return 0;
}
