package main

/*
#include <stdlib.h>
#include <stdint.h>
*/
import "C"
import (
	"crypto/sha256"
	"fmt"
	"runtime"
	"sync"
	"unsafe"
)

//export process_payload_go
func process_payload_go(payload *C.char) *C.char {
	goStr := C.GoString(payload)
	hash := sha256.Sum256([]byte(goStr))
	return C.CString(fmt.Sprintf("%x", hash))
}

//export free_string_go
func free_string_go(s *C.char) {
}

// PHASE 4: ZERO-COPY MMAP BFT CONSENSUS
//export process_mmap_go
func process_mmap_go(inPtr unsafe.Pointer, outPtr unsafe.Pointer, numRecords C.size_t, recordSize C.size_t, hashSize C.size_t) {
	num := int(numRecords)
	recSz := int(recordSize)
	hashSz := int(hashSize)

	// Create slices that map directly to the C memory
	inBytes := unsafe.Slice((*byte)(inPtr), num*recSz)
	outBytes := unsafe.Slice((*byte)(outPtr), num*hashSz)

	numCPU := runtime.NumCPU()
	var wg sync.WaitGroup

	// Simple chunking for goroutines
	chunkSize := num / numCPU
	if chunkSize == 0 {
		chunkSize = 1
	}

	for i := 0; i < numCPU; i++ {
		startIdx := i * chunkSize
		endIdx := startIdx + chunkSize
		if i == numCPU-1 {
			endIdx = num
		}
		if startIdx >= num {
			break
		}

		wg.Add(1)
		go func(start, end int) {
			defer wg.Done()
			for j := start; j < end; j++ {
				inStart := j * recSz
				inEnd := inStart + recSz
				
				outStart := j * hashSz
				
				hash := sha256.Sum256(inBytes[inStart:inEnd])
				copy(outBytes[outStart:outStart+hashSz], hash[:])
			}
		}(startIdx, endIdx)
	}

	wg.Wait()
}

func main() {}
