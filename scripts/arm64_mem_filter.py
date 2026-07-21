import subprocess
import re
import sys
from typing import Dict, Any, List

def get_process_memory_map(pid: int) -> List[Dict[str, Any]]:
    """
    [C5-REAL] Extrae y filtra el mapa de memoria del proceso en macOS.
    Excluye explícitamente el Shared Cache y retiene solo páginas R/W.
    """
    try:
        # Require sudo/entitlements for task_for_pid
        result = subprocess.run(
            ['vmmap', str(pid)], 
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error executing vmmap: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    lines = result.stdout.split('\n')
    filtered_regions = []
    
    # Regex for parsing vmmap output (Region, Start-End, [size], r/w/x permissions)
    # Example line: MALLOC_LARGE       0000000105000000-0000000105100000 [ 1024K] rw-/rwx SM=PRV  
    region_regex = re.compile(
        r'^(?P<type>[\w\_]+.*?)\s+(?P<start>[0-9a-fA-F]+)-(?P<end>[0-9a-fA-F]+)\s+\[\s*(?P<size>.*?)\s*\]\s+(?P<perms>[rwx\-]{3}/[rwx\-]{3})\s+(?P<details>.*)$'
    )

    for line in lines:
        match = region_regex.match(line)
        if match:
            region_data = match.groupdict()
            perms = region_data['perms'].split('/')[0] # Current permissions
            
            # C5-REAL FILTERING LOGIC:
            # 1. Must be Read/Write
            # 2. Must not be in the Shared Cache (usually __TEXT, __LINKEDIT of system libs)
            # 3. Focus on heap, malloc, and anonymous memory
            
            is_rw = 'r' in perms and 'w' in perms
            is_shared_cache = 'shared' in region_data['details'].lower() or 'SM=SHM' in region_data['details']
            
            if is_rw and not is_shared_cache:
                filtered_regions.append({
                    "type": region_data['type'].strip(),
                    "start": hex(int(region_data['start'], 16)),
                    "end": hex(int(region_data['end'], 16)),
                    "size": region_data['size'].strip(),
                    "permissions": perms
                })

    return filtered_regions

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python arm64_mem_filter.py <PID>")
        sys.exit(1)
        
    pid = int(sys.argv[1])
    regions = get_process_memory_map(pid)
    
    print(f"[C5-REAL] Regiones R/W extraidas (Excluyendo Shared Cache) para PID {pid}: {len(regions)}")
    for r in regions:
        print(f"{r['start']} - {r['end']} | Size: {r['size']} | Type: {r['type']}")
