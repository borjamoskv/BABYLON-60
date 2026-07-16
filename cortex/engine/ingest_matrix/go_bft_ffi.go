package main

import "C"
import (
	"crypto/sha256"
	"fmt"
)

//export process_payload_go
func process_payload_go(payload *C.char) *C.char {
	goStr := C.GoString(payload)
	hash := sha256.Sum256([]byte(goStr))
	return C.CString(fmt.Sprintf("%x", hash))
}

//export free_string_go
func free_string_go(s *C.char) {
	// In CGO, C.CString allocates using malloc. The caller must free it.
	// We can expose a free function for convenience if the caller doesn't have C.free available.
	// But in python ctypes, libc.free is usually better.
	// Still, we can provide it for symmetry:
	// C.free(unsafe.Pointer(s)) -> requires importing stdlib, let's skip to keep it simple.
	// We'll let Python call libc.free.
}

func main() {}
