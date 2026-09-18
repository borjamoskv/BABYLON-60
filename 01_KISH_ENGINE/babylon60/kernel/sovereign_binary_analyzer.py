# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ SOVEREIGN BINARY ANALYZER & CFG ENGINE | STATE: C5-REAL
# ============================================================================
"""
sovereign_binary_analyzer.py — Native Executable Parser & Control Flow Graph Engine.
Provides zero-dependency Mach-O (macOS) and ELF (Linux) binary disassembly,
Basic Block fragmentation, Control Flow Graph (CFG) generation, and interactive
Mermaid / HTML visualization for BABYLON-60.
"""

import os
import sys
import struct
import re
import subprocess
import html
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

# Optional Capstone import
try:
    import capstone

    HAS_CAPSTONE = True
except ImportError:
    HAS_CAPSTONE = False


@dataclass
class Instruction:
    address: int
    mnemonic: str
    op_str: str
    bytes_hex: str
    is_branch: bool = False
    is_call: bool = False
    is_ret: bool = False
    target_address: Optional[int] = None


@dataclass
class BasicBlock:
    id: str
    start_address: int
    end_address: int
    instructions: List[Instruction] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)


@dataclass
class SectionInfo:
    name: str
    address: int
    size: int
    offset: int
    flags: int


@dataclass
class BinaryMetadata:
    filename: str
    format: str  # "Mach-O 64", "ELF 64", "Fat Mach-O", "Unknown"
    architecture: str  # "arm64", "x86_64", "unknown"
    entry_point: int
    sections: List[SectionInfo] = field(default_factory=list)


class SovereignBinaryAnalyzer:
    """Sovereign Binary Parser, Disassembler, and Control Flow Graph Engine."""

    # Mach-O Constants
    MH_MAGIC_64 = 0xFEEDFACF
    MH_CIGAM_64 = 0xCFFAEDFE
    FAT_MAGIC = 0xCAFEBABE
    FAT_CIGAM = 0xBEBAFECA

    # ELF Constants
    ELF_MAGIC = b"\x7fELF"

    def __init__(self, filepath: str) -> None:
        self.filepath = os.path.abspath(filepath)
        if not os.path.isfile(self.filepath):
            raise FileNotFoundError(f"Binary file not found: {self.filepath}")

        self.metadata = self._parse_metadata()

    def _parse_metadata(self) -> BinaryMetadata:
        """Parse basic headers for Mach-O or ELF 64-bit binaries."""
        with open(self.filepath, "rb") as f:
            header_bytes = f.read(64)

        if len(header_bytes) < 32:
            return BinaryMetadata(os.path.basename(self.filepath), "Unknown", "unknown", 0)

        # 1. Check Mach-O 64-bit
        magic = struct.unpack("<I", header_bytes[:4])[0]
        if magic in (self.MH_MAGIC_64, self.MH_CIGAM_64):
            return self._parse_macho_64(header_bytes)

        # 2. Check Fat Mach-O
        if magic in (self.FAT_MAGIC, self.FAT_CIGAM):
            return BinaryMetadata(os.path.basename(self.filepath), "Fat Mach-O", "multi", 0)

        # 3. Check ELF
        if header_bytes[:4] == self.ELF_MAGIC:
            return self._parse_elf_64(header_bytes)

        return BinaryMetadata(os.path.basename(self.filepath), "Raw Binary", "unknown", 0)

    def _parse_macho_64(self, header_bytes: bytes) -> BinaryMetadata:
        """Parse Mach-O 64-bit header."""
        magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, reserved = struct.unpack(
            "<IIIIIIII", header_bytes[:32]
        )

        arch = "x86_64"
        if cputype == 0x0100000C:  # CPU_TYPE_ARM64
            arch = "arm64"
        elif cputype == 0x01000007:  # CPU_TYPE_X86_64
            arch = "x86_64"

        sections: List[SectionInfo] = []

        with open(self.filepath, "rb") as f:
            f.seek(32)  # Skip mach_header_64
            cmd_data = f.read(sizeofcmds)

        offset = 0
        for _ in range(ncmds):
            if offset + 8 > len(cmd_data):
                break
            cmd, cmdsize = struct.unpack("<II", cmd_data[offset : offset + 8])

            # LC_SEGMENT_64 = 0x19
            if cmd == 0x19 and offset + 72 <= len(cmd_data):
                _segname = cmd_data[offset + 8 : offset + 24].decode("utf-8", "ignore").rstrip("\x00")
                vmaddr, vmsize, fileoff, filesize, maxprot, initprot, nsects, flags = struct.unpack(
                    "<QQQQIIII", cmd_data[offset + 24 : offset + 72]
                )

                sect_offset = offset + 72
                for s in range(nsects):
                    if sect_offset + 80 <= len(cmd_data):
                        sectname = cmd_data[sect_offset : sect_offset + 16].decode("utf-8", "ignore").rstrip("\x00")
                        s_vmname = (
                            cmd_data[sect_offset + 16 : sect_offset + 32].decode("utf-8", "ignore").rstrip("\x00")
                        )
                        addr, size, off, align, reloff, nreloc, s_flags = struct.unpack(
                            "<QQIIIII", cmd_data[sect_offset + 32 : sect_offset + 68]
                        )
                        sections.append(SectionInfo(f"{s_vmname}:{sectname}", addr, size, off, s_flags))
                        sect_offset += 80

            offset += cmdsize

        return BinaryMetadata(
            filename=os.path.basename(self.filepath),
            format="Mach-O 64",
            architecture=arch,
            entry_point=sections[0].address if sections else 0,
            sections=sections,
        )

    def _parse_elf_64(self, header_bytes: bytes) -> BinaryMetadata:
        """Parse ELF 64-bit header."""
        _ei_class = header_bytes[4]
        ei_data = header_bytes[5]
        endian = "<" if ei_data == 1 else ">"

        e_type, e_machine, e_version, e_entry = struct.unpack(f"{endian}HHIQ", header_bytes[16:32])

        arch = "x86_64" if e_machine == 62 else ("arm64" if e_machine == 183 else f"arch_{e_machine}")

        return BinaryMetadata(
            filename=os.path.basename(self.filepath),
            format="ELF 64",
            architecture=arch,
            entry_point=e_entry,
            sections=[],
        )

    def disassemble_section(self, section_name: str = "__text", max_instructions: int = 500) -> List[Instruction]:
        """Extract and disassemble a code section using Capstone or system tools."""
        instructions: List[Instruction] = []

        # Try Capstone first if available
        if HAS_CAPSTONE:
            instructions = self._disassemble_capstone(section_name, max_instructions)

        # Fallback to system otool / objdump if Capstone is not present or failed
        if not instructions:
            instructions = self._disassemble_system_cli(max_instructions)

        return instructions

    def _disassemble_capstone(self, section_name: str, max_instructions: int) -> List[Instruction]:
        """Disassemble using Capstone library."""
        code_bytes = b""
        start_addr = 0

        # Find target section
        for sec in self.metadata.sections:
            if section_name in sec.name or sec.name.endswith(section_name):
                with open(self.filepath, "rb") as f:
                    f.seek(sec.offset)
                    code_bytes = f.read(sec.size)
                start_addr = sec.address
                break

        if not code_bytes:
            return []

        arch_cs = capstone.CS_ARCH_ARM64 if self.metadata.architecture == "arm64" else capstone.CS_ARCH_X86
        mode_cs = capstone.CS_MODE_ARM if self.metadata.architecture == "arm64" else capstone.CS_MODE_64

        md = capstone.Cs(arch_cs, mode_cs)
        md.detail = True

        instructions: List[Instruction] = []
        for i, insn in enumerate(md.disasm(code_bytes, start_addr)):
            if i >= max_instructions:
                break

            mnemonic = insn.mnemonic.lower()
            op_str = insn.op_str.lower()

            is_branch = mnemonic in (
                "b",
                "b.eq",
                "b.ne",
                "b.gt",
                "b.lt",
                "cbz",
                "cbnz",
                "tbz",
                "tbnz",
                "jmp",
                "je",
                "jne",
                "jg",
                "jl",
            )
            is_call = mnemonic in ("bl", "blr", "call")
            is_ret = mnemonic in ("ret", "rets")

            target_addr = None
            if is_branch or is_call:
                match = re.search(r"0x[0-9a-fA-F]+", op_str)
                if match:
                    target_addr = int(match.group(0), 16)

            instructions.append(
                Instruction(
                    address=insn.address,
                    mnemonic=mnemonic,
                    op_str=op_str,
                    bytes_hex=insn.bytes.hex(),
                    is_branch=is_branch,
                    is_call=is_call,
                    is_ret=is_ret,
                    target_address=target_addr,
                )
            )

        return instructions

    def _disassemble_system_cli(self, max_instructions: int) -> List[Instruction]:
        """Fallback disassembly via system otool or objdump CLI."""
        cmd = ["otool", "-tv", self.filepath] if sys.platform == "darwin" else ["objdump", "-d", self.filepath]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            output = res.stdout
        except Exception:
            return []

        instructions: List[Instruction] = []
        for line in output.splitlines():
            line = line.strip()
            if not line or ":" in line and not line.startswith("0x"):
                continue

            parts = line.split(maxsplit=2)
            if len(parts) >= 2:
                try:
                    addr_str = parts[0].rstrip(":")
                    addr = int(addr_str, 16)
                    mnemonic = parts[1].lower()
                    op_str = parts[2].lower() if len(parts) > 2 else ""

                    is_branch = mnemonic in (
                        "b",
                        "b.eq",
                        "b.ne",
                        "b.gt",
                        "b.lt",
                        "cbz",
                        "cbnz",
                        "jmp",
                        "je",
                        "jne",
                        "jg",
                        "jl",
                    )
                    is_call = mnemonic in ("bl", "blr", "call")
                    is_ret = mnemonic in ("ret", "rets")

                    target_addr = None
                    if is_branch or is_call:
                        match = re.search(r"0x[0-9a-fA-F]+", op_str)
                        if match:
                            target_addr = int(match.group(0), 16)

                    instructions.append(
                        Instruction(
                            address=addr,
                            mnemonic=mnemonic,
                            op_str=op_str,
                            bytes_hex="",
                            is_branch=is_branch,
                            is_call=is_call,
                            is_ret=is_ret,
                            target_address=target_addr,
                        )
                    )
                    if len(instructions) >= max_instructions:
                        break
                except ValueError:
                    continue

        return instructions

    def build_cfg(self, instructions: List[Instruction]) -> Dict[str, BasicBlock]:
        """Partition instructions into Basic Blocks and link control flow edges."""
        if not instructions:
            return {}

        leaders: Set[int] = {instructions[0].address}
        addr_map = {insn.address: i for i, insn in enumerate(instructions)}

        for i, insn in enumerate(instructions):
            if insn.is_branch or insn.is_call or insn.is_ret:
                if i + 1 < len(instructions):
                    leaders.add(instructions[i + 1].address)
                if insn.target_address and insn.target_address in addr_map:
                    leaders.add(insn.target_address)

        sorted_leaders = sorted(list(leaders))
        blocks: Dict[str, BasicBlock] = {}

        for idx, leader in enumerate(sorted_leaders):
            start_i = addr_map[leader]
            next_leader = sorted_leaders[idx + 1] if idx + 1 < len(sorted_leaders) else None
            end_i = addr_map[next_leader] if next_leader and next_leader in addr_map else len(instructions)

            block_insns = instructions[start_i:end_i]
            block_id = f"block_{hex(leader)}"

            blocks[block_id] = BasicBlock(
                id=block_id,
                start_address=leader,
                end_address=block_insns[-1].address if block_insns else leader,
                instructions=block_insns,
            )

        for block_id, block in blocks.items():
            if not block.instructions:
                continue

            last_insn = block.instructions[-1]

            if last_insn.is_branch:
                if last_insn.target_address:
                    target_id = f"block_{hex(last_insn.target_address)}"
                    if target_id in blocks:
                        block.successors.append(target_id)
                        blocks[target_id].predecessors.append(block_id)

                if last_insn.mnemonic not in ("b", "jmp"):
                    next_addr_idx = addr_map.get(last_insn.address, 0) + 1
                    if next_addr_idx < len(instructions):
                        fall_id = f"block_{hex(instructions[next_addr_idx].address)}"
                        if fall_id in blocks and fall_id not in block.successors:
                            block.successors.append(fall_id)
                            blocks[fall_id].predecessors.append(block_id)

            elif not last_insn.is_ret:
                next_addr_idx = addr_map.get(last_insn.address, 0) + 1
                if next_addr_idx < len(instructions):
                    fall_id = f"block_{hex(instructions[next_addr_idx].address)}"
                    if fall_id in blocks:
                        block.successors.append(fall_id)
                        blocks[fall_id].predecessors.append(block_id)

        return blocks

    def render_mermaid_html(self, blocks: Dict[str, BasicBlock], output_file: str) -> str:
        """Render CFG as an interactive HTML document with Mermaid.js graph."""
        mermaid_lines = ["graph TD"]

        for b_id, block in blocks.items():
            insn_lines = [f"{hex(ins.address)}: {ins.mnemonic} {ins.op_str}" for ins in block.instructions[:6]]
            if len(block.instructions) > 6:
                insn_lines.append(f"... (+{len(block.instructions) - 6} insns)")

            block_label = f"<b>{b_id}</b><br/>" + "<br/>".join(insn_lines)
            block_label_escaped = (
                html.escape(block_label)
                .replace("&lt;br/&gt;", "<br/>")
                .replace("&lt;b&gt;", "<b>")
                .replace("&lt;/b&gt;", "</b>")
            )

            mermaid_lines.append(f'    {b_id}["{block_label_escaped}"]')

            for succ in block.successors:
                mermaid_lines.append(f"    {b_id} --> {succ}")

        mermaid_code = "\n".join(mermaid_lines)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BABYLON-60 Sovereign CFG — {html.escape(self.metadata.filename)}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.min.js"></script>
    <style>
        body {{
            background-color: #0f1419;
            color: #e6edf3;
            font-family: 'Geist Mono', ui-monospace, monospace;
            padding: 20px;
        }}
        .header {{
            background: #161b22;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #30363d;
            margin-bottom: 20px;
        }}
        .header h1 {{ margin: 0 0 10px 0; color: #58a6ff; font-size: 20px; }}
        .meta-tag {{
            display: inline-block;
            background: #21262d;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 10px;
            border: 1px solid #30363d;
        }}
        .diagram-container {{
            background: #161b22;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #30363d;
            overflow: auto;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>BABYLON-60 Sovereign Binary Control Flow Graph</h1>
        <div>
            <span class="meta-tag"><b>File:</b> {html.escape(self.metadata.filename)}</span>
            <span class="meta-tag"><b>Format:</b> {html.escape(self.metadata.format)}</span>
            <span class="meta-tag"><b>Arch:</b> {html.escape(self.metadata.architecture)}</span>
            <span class="meta-tag"><b>Blocks:</b> {len(blocks)}</span>
        </div>
    </div>
    <div class="diagram-container">
        <pre class="mermaid">
{mermaid_code}
        </pre>
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    </script>
</body>
</html>
"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file
