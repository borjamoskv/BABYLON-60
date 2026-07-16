import ctypes
import os
import time

def setup_rust_lib():
    lib_path = "target/release/librust_ingest_ffi.dylib"
    if not os.path.exists(lib_path):
        print(f"FATAL: Rust C-FFI Payload missing at {lib_path}. Compile via 'cargo build --release'.")
        return None

    rust_lib = ctypes.CDLL(os.path.abspath(lib_path))
    rust_lib.process_mmap_rust.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t
    ]
    rust_lib.process_mmap_rust.restype = None
    return rust_lib

def setup_go_lib():
    lib_path = "libgo_ingest_ffi.dylib"
    if not os.path.exists(lib_path):
        print(f"FATAL: Go C-FFI Payload missing at {lib_path}. Compile via 'go build -buildmode=c-shared'.")
        return None

    go_lib = ctypes.CDLL(os.path.abspath(lib_path))
    go_lib.process_mmap_go.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t
    ]
    go_lib.process_mmap_go.restype = None
    return go_lib

def main():
    print("[C5-REAL] IGNITING PHASE 4: ZERO-COPY MMAP BFT CONSENSUS...")
    rust_lib = setup_rust_lib()
    go_lib = setup_go_lib()

    ITERATIONS = 1_000_000
    RECORD_SIZE = 32
    HASH_SIZE = 32

    # Allocate a massive contiguous memory block in Python
    # This bypasses the GIL entirely by letting native languages read raw RAM
    print(f"[C5-REAL] Allocating raw contiguous memory for {ITERATIONS} records...")
    in_buffer = (ctypes.c_uint8 * (ITERATIONS * RECORD_SIZE))()
    rust_out_buffer = (ctypes.c_uint8 * (ITERATIONS * HASH_SIZE))()
    go_out_buffer = (ctypes.c_uint8 * (ITERATIONS * HASH_SIZE))()

    # Pre-fill with some data (simulate incoming network buffer)
    # We do a fast memory initialization
    ctypes.memset(ctypes.addressof(in_buffer), 0xAA, ctypes.sizeof(in_buffer))

    in_ptr = ctypes.cast(in_buffer, ctypes.c_void_p)
    rust_out_ptr = ctypes.cast(rust_out_buffer, ctypes.c_void_p)
    go_out_ptr = ctypes.cast(go_out_buffer, ctypes.c_void_p)

    if rust_lib:
        print("[C5-REAL] Rust Engine processing 1M Memory Mapped Payloads...")
        start_time = time.time()
        rust_lib.process_mmap_rust(in_ptr, rust_out_ptr, ITERATIONS, RECORD_SIZE, HASH_SIZE)
        end_time = time.time()
        print(f"[C5-REAL] RUST MMAP Processed {ITERATIONS} payloads in {end_time - start_time:.4f} seconds.")

    if go_lib:
        print("[C5-REAL] Go Engine processing 1M Memory Mapped Payloads...")
        start_time = time.time()
        go_lib.process_mmap_go(in_ptr, go_out_ptr, ITERATIONS, RECORD_SIZE, HASH_SIZE)
        end_time = time.time()
        print(f"[C5-REAL] GO MMAP Processed {ITERATIONS} payloads in {end_time - start_time:.4f} seconds.")

    # Validate BFT consensus (Isomorphism Check)
    if rust_lib and go_lib:
        print("[C5-REAL] Verifying Zero-Copy BFT Consensus Isomorphism...")
        start_time = time.time()
        
        # Compare the raw memory byte by byte using ctypes
        rust_mem = ctypes.string_at(rust_out_ptr, ITERATIONS * HASH_SIZE)
        go_mem = ctypes.string_at(go_out_ptr, ITERATIONS * HASH_SIZE)
        
        if rust_mem == go_mem:
            print(f"[C5-REAL] CONSENSUS ACHIEVED: Memory states match perfectly (Time: {time.time() - start_time:.4f}s).")
        else:
            print("[C5-REAL] FATAL: Entropy detected! Memory states do NOT match.")

if __name__ == '__main__':
    main()
