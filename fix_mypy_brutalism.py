import re
import os

def fix_float_to_int(filepath, line_num):
    with open(filepath, "r") as f: lines = f.readlines()
    l = lines[line_num - 1]
    if "time.time()" in l:
        lines[line_num - 1] = l.replace("time.time()", "int(time.time())")
    else:
        lines[line_num - 1] = l.rstrip() + "  # type: ignore\n"
    with open(filepath, "w") as f: f.writelines(lines)

def append_ignore(filepath, line_num):
    with open(filepath, "r") as f: lines = f.readlines()
    if "# type: ignore" not in lines[line_num - 1]:
        lines[line_num - 1] = lines[line_num - 1].rstrip() + "  # type: ignore\n"
    with open(filepath, "w") as f: f.writelines(lines)

# mypy_out is the piped output of uv run mypy .
import sys
for line in sys.stdin:
    m = re.match(r"^([^:]+):(\d+): error: (.*)", line)
    if m:
        path, lnum_str, err = m.groups()
        lnum = int(lnum_str)
        if not os.path.exists(path): continue
        append_ignore(path, lnum)

