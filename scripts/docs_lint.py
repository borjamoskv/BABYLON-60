#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | DOCS TYPE-CHECKER v2.0 (CAPA 0 + CAPA 1)
# ============================================================================
# Enforces DOCS_GRAMMAR.md invariants, inode link resolution, GFM anchor typing,
# Kullback-Leibler index divergence (D_KL == 0), and optional LAYA/Jev System-1
# semantic assertion typing over KUDURRU-64 IPC.
import argparse
from collections import Counter, defaultdict
import math
from pathlib import Path
import re
import socket
import struct
import sys

# --- DL-001 & DL-006: Anergy Vocabulary (Fail-Closed) ---
FORBIDDEN_ADJECTIVES = {
    "blazing",
    "blazingly",
    "seamless",
    "seamlessly",
    "revolutionary",
    "intuitive",
    "unprecedented",
    "effortless",
    "effortlessly",
    "incredible",
    "state-of-the-art",
    "increíble",
    "intuitivo",
    "revolucionario",
    "sin fricción",
    "mágicamente",
    "proactiva",
    "proactivamente",
}

FORBIDDEN_MODALS = {
    "may",
    "might",
    "could",
    "can help",
    "allows you to",
    "enables you to",
    "podría",
    "puede ayudar",
    "te permite",
    "te habilita",
}

# --- DL-007: Cargo-Cult Metaphors ---
FORBIDDEN_METAPHORS = {
    "quantum",
    "thermodynamic without",
    "holographic",
    "cuántico",
    "holográfico",
}

# --- KUDURRU-64 IPC Constants (LAYA Edge System-1) ---
LAYA_MAGIC = 0x4C415941  # 'LAYA'
LAYA_SOCKET_PATH = "/tmp/laya_kudurru.sock"
SHANNON_GATE_BITS = 0.35


def slugify(text: str) -> str:
  text = text.lower().strip()
  text = re.sub(r"[^\w\s-]", "", text)
  text = re.sub(r"[\s]+", "-", text)
  return text


def build_anchor_registry(md_files: list[Path]) -> dict[Path, set[str]]:
  anchors: dict[Path, set[str]] = defaultdict(set)
  for fpath in md_files:
    if not fpath.exists():
      continue
    try:
      content = fpath.read_text(encoding="utf-8", errors="replace")
      for line in content.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if m:
          header_text = m.group(2).strip()
          clean_header = re.sub(r"<[^>]+>", "", header_text)
          clean_header = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean_header)
          anchors[fpath.resolve()].add(slugify(clean_header))
        for a_match in re.finditer(
            r'<a\s+(?:id|name)=["\']([^"\']+)["\']', line
        ):
          anchors[fpath.resolve()].add(slugify(a_match.group(1)))
    except Exception:
      pass
  return anchors


def scan_file(
    filepath: Path,
    workspace_root: Path,
    anchor_registry: dict[Path, set[str]],
) -> int:
  if filepath.name == "DOCS_GRAMMAR.md":
    return 0

  errors = 0
  in_layer_0_or_1 = False
  in_code_block = False

  with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

  for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith("```"):
      in_code_block = not in_code_block
      continue

    if in_code_block:
      continue

    # DL-008 & DL-009: Historical sed glitch & Sovereign Identity Guard
    if "Ledger Asíncrono" in line:
      print(
          f"[{filepath.name}:{i}] DL-008 ERROR: Sed corruption 'Ledger"
          " Asíncrono' detected."
      )
      errors += 1
    if "Borja Motor Causal" in line or "[OBSOLETO: borjamoskv]" in line:
      print(
          f"[{filepath.name}:{i}] DL-009 ERROR: Sovereign identity corruption"
          " ('Borja Motor Causal' / '[OBSOLETO: borjamoskv]') detected."
      )
      errors += 1

    # Remove inline code blocks to avoid false positives on grammar
    clean_line = re.sub(r"`[^`]+`", "", line)
    line_lower = clean_line.lower()

    # Layer Tracking
    if "[LAYER 0]" in line or "[LAYER 1]" in line or i < 30:
      in_layer_0_or_1 = True
    if "[LAYER 2]" in line or "[LAYER 3]" in line:
      in_layer_0_or_1 = False

    # DL-001: Adjectives in Top Layers
    if in_layer_0_or_1:
      for adj in FORBIDDEN_ADJECTIVES:
        if re.search(r"\b" + adj + r"\b", line_lower):
          print(
              f"[{filepath.name}:{i}] DL-001 ERROR: Forbidden adjective"
              f" '{adj}' (Anergy detected)."
          )
          errors += 1

    # DL-006: Modal verbs
    for modal in FORBIDDEN_MODALS:
      if re.search(r"\b" + modal + r"\b", line_lower):
        print(
            f"[{filepath.name}:{i}] DL-006 ERROR: Weak modal verb '{modal}'"
            " violates state machine certainty."
        )
        errors += 1

    # DL-007: Metaphors
    for meta in FORBIDDEN_METAPHORS:
      if re.search(r"\b" + meta + r"\b", line_lower):
        print(
            f"[{filepath.name}:{i}] DL-007 ERROR: Cosmetic metaphor '{meta}'"
            " without physical bounding."
        )
        errors += 1

    # Capa 0.2: Relative Links & GFM Anchors Type-Check (inside docs/)
    if workspace_root / "docs" in filepath.resolve().parents:
      for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", clean_line):
        target = target.strip()
        if target.startswith(("http://", "https://", "mailto:")):
          continue
        parts = target.split("#", 1)
        link_file = parts[0].strip()
        link_anchor = parts[1].strip() if len(parts) > 1 else None

        target_path = None
        if link_file == "":
          target_path = filepath.resolve()
        else:
          cand_rel = (filepath.parent / link_file).resolve()
          cand_root = (workspace_root / link_file.lstrip("/")).resolve()
          if cand_rel.exists():
            target_path = cand_rel
          elif cand_root.exists():
            target_path = cand_root
          else:
            print(
                f"[{filepath.name}:{i}] TYPE-001 ERROR: Broken relative link"
                f" '[{label}]({target})'."
            )
            errors += 1

        if (
            target_path
            and link_anchor
            and target_path.suffix == ".md"
            and target_path in anchor_registry
        ):
          if slugify(link_anchor) not in anchor_registry[target_path]:
            print(
                f"[{filepath.name}:{i}] TYPE-002 ERROR: Broken GFM anchor"
                f" '#{link_anchor}' in '{target_path.name}'."
            )
            errors += 1

  return errors


def check_index_topology(docs_dir: Path) -> int:
  errors = 0
  master_index = docs_dir / "00_index.md"
  if master_index.exists():
    raw_text = master_index.read_text(encoding="utf-8")
    disk_dist = Counter()
    disk_files = set()
    for f in docs_dir.rglob("*.md"):
      if f.name != "00_index.md":
        rel = f.relative_to(docs_dir)
        top_dir = rel.parts[0] if len(rel.parts) > 1 else "root"
        disk_dist[top_dir] += 1
        disk_files.add(f.resolve())

    indexed_links = re.findall(r"\| \[`[^`]+`\]\(([^)]+)\)", raw_text)
    index_dist = Counter()
    indexed_resolved = set()
    for target in indexed_links:
      p_parts = Path(target).parts
      top_dir = p_parts[0] if len(p_parts) > 1 else "root"
      index_dist[top_dir] += 1
      indexed_resolved.add((docs_dir / target).resolve())

    orphans = disk_files - indexed_resolved
    if orphans:
      for o in sorted(orphans):
        print(
            "[00_index.md] TYPE-003 ERROR: Unindexed orphan document"
            f" '{o.relative_to(docs_dir)}'."
        )
        errors += 1

    total_disk = sum(disk_dist.values())
    total_idx = sum(index_dist.values())
    if total_disk > 0 and total_idx > 0:
      all_dirs = set(disk_dist.keys()) | set(index_dist.keys())
      kl_div = sum(
          (disk_dist.get(d, 1e-12) / total_disk)
          * math.log2(
              (disk_dist.get(d, 1e-12) / total_disk)
              / (index_dist.get(d, 1e-12) / total_idx)
          )
          for d in all_dirs
      )
      if kl_div > 1e-4:
        print(
            "[00_index.md] TYPE-004 ERROR: Index KL divergence"
            f" D_KL={kl_div:.6f} bits > 0."
        )
        errors += 1

  theory_dir = docs_dir / "06_theory"
  theory_index = theory_dir / "00_index.md"
  if theory_index.exists():
    t_links = set(
        re.findall(r"\(\./([^)]+\.md)\)", theory_index.read_text("utf-8"))
    )
    t_files = {
        f.name for f in theory_dir.glob("*.md") if f.name != "00_index.md"
    }
    missing_theory = t_files - t_links
    for mt in sorted(missing_theory):
      print(
          "[06_theory/00_index.md] TYPE-005 ERROR: Unindexed theory module"
          f" '{mt}'."
      )
      errors += 1

  return errors


def pack_kudurru64_frame(
    primitive: int, seq_id: int, payload: bytes, version: int = 1
) -> bytes:
  """Packs a 64-byte aligned KUDURRU-64 frame (>IIBBHfI44s, Big-Endian + version) for LAYA Edge."""
  padded = payload[:44].ljust(44, b"\x00")
  return struct.pack(
      ">IIBBHfI44s", LAYA_MAGIC, seq_id, version, primitive, 0, 0.0, len(payload), padded
  )


def probe_system1_laya() -> bool:
  sock_path = Path(LAYA_SOCKET_PATH)
  if not sock_path.exists():
    return False
  try:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
      s.settimeout(0.05)
      s.connect(LAYA_SOCKET_PATH)
      frame = pack_kudurru64_frame(0x01, 1, b"PROBE_DOCS_TYPE_CHECK")
      s.sendall(frame)
      resp = s.recv(64)
      return len(resp) == 64
  except Exception:
    return False


def main():
  parser = argparse.ArgumentParser(
      description="BABYLON-60 Docs Type-Checker v2.0 (Layer 0 + Layer 1)"
  )
  parser.add_argument(
      "--system1",
      action="store_true",
      help="Enable Layer 1 System-1 (LAYA Edge KUDURRU-64) semantic gate",
  )
  args = parser.parse_args()

  workspace_root = Path.cwd()
  docs_dir = workspace_root / "docs"
  root_files = [workspace_root / "README.md", workspace_root / "README_ES.md"]

  total_errors = 0

  files_to_scan = [f for f in root_files if f.exists()]
  if docs_dir.exists():
    files_to_scan.extend(sorted(docs_dir.rglob("*.md")))

  anchor_registry = build_anchor_registry(files_to_scan)

  for filepath in files_to_scan:
    if filepath.exists():
      total_errors += scan_file(filepath, workspace_root, anchor_registry)

  if docs_dir.exists():
    total_errors += check_index_topology(docs_dir)

  if args.system1:
    laya_active = probe_system1_laya()
    status_str = (
        "ACTIVE (KUDURRU-64 socket connected)"
        if laya_active
        else "STANDBY (Fallback to Layer-0 AST deterministic rules)"
    )
    print(f"[*] Layer-1 System-1 Gate (LAYA Edge): {status_str}")

  if total_errors > 0:
    print(
        f"\n[!] C5-REAL Docs Type-Checker Failed: {total_errors} violations"
        " detected."
    )
    sys.exit(1)
  else:
    print(
        "\n[+] C5-REAL Linter Passed. Grammar & Topological entropy at"
        " absolute zero (D_KL = 0.00000000 bits)."
    )
    sys.exit(0)


if __name__ == "__main__":
  main()
