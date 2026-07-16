import ctypes
import os
import time

def setup_rust_lib():
    lib_path = "target/release/librust_ingest_ffi.dylib"
    if not os.path.exists(lib_path):
        print(f"FATAL: Rust C-FFI Payload missing at {lib_path}. Compile via 'cargo build --release'.")
        return None

    rust_lib = ctypes.CDLL(os.path.abspath(lib_path))
    rust_lib.process_payload_rust.argtypes = [ctypes.c_char_p]
    rust_lib.process_payload_rust.restype = ctypes.POINTER(ctypes.c_char)
    rust_lib.free_string_rust.argtypes = [ctypes.POINTER(ctypes.c_char)]
    return rust_lib

def setup_go_lib():
    lib_path = "libgo_ingest_ffi.dylib"
    if not os.path.exists(lib_path):
        print(f"FATAL: Go C-FFI Payload missing at {lib_path}. Compile via 'go build -buildmode=c-shared'.")
        return None

    go_lib = ctypes.CDLL(os.path.abspath(lib_path))
    go_lib.process_payload_go.argtypes = [ctypes.c_char_p]
    go_lib.process_payload_go.restype = ctypes.POINTER(ctypes.c_char)
    
    # We use libc free for Go CString
    libc = ctypes.CDLL("libc.dylib")
    libc.free.argtypes = [ctypes.c_void_p]
    go_lib.free_string = libc.free
    return go_lib

def main():
    print("[C5-REAL] IGNITING C-FFI GIL BYPASS ARENA (Rust vs Go)...")
    rust_lib = setup_rust_lib()
    go_lib = setup_go_lib()

    ITERATIONS = 10000

    if rust_lib:
        start_time = time.time()
        for i in range(ITERATIONS):
            payload = f"PAYLOAD_PYTHON_{i}".encode('utf-8')
            ptr = rust_lib.process_payload_rust(payload)
            result = ctypes.cast(ptr, ctypes.c_char_p).value.decode('utf-8')
            rust_lib.free_string_rust(ptr)
        end_time = time.time()
        print(f"[C5-REAL] RUST FFI Processed {ITERATIONS} payloads in {end_time - start_time:.4f} seconds.")
        print(f"[C5-REAL] RUST Terminal Hash: {result}")

    if go_lib:
        start_time = time.time()
        for i in range(ITERATIONS):
            payload = f"PAYLOAD_PYTHON_{i}".encode('utf-8')
            ptr = go_lib.process_payload_go(payload)
            result = ctypes.cast(ptr, ctypes.c_char_p).value.decode('utf-8')
            go_lib.free_string(ptr)
        end_time = time.time()
        print(f"[C5-REAL] GO FFI Processed {ITERATIONS} payloads in {end_time - start_time:.4f} seconds.")
        print(f"[C5-REAL] GO Terminal Hash: {result}")

if __name__ == '__main__':
    main()
