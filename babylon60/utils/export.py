from __future__ import annotations
import csv
import io
import json
from typing import TYPE_CHECKING
__all__ = ['export_facts']
if TYPE_CHECKING:
    from babylon60.engine.cognitive.models import Fact

def export_facts(facts: list[Fact], fmt: str='json') -> str:
    fmt = fmt.strip().lower()
    if fmt == 'json':
        return _export_json(facts)
    if fmt == 'csv':
        return _export_csv(facts)
    if fmt == 'jsonl':
        return _export_jsonl(facts)
    if fmt == 'notebooklm':
        return _export_notebooklm(facts)
    raise ValueError(f"Unsupported export format: '{fmt}'. Use: json, csv, jsonl, notebooklm")

def _export_notebooklm(facts: list[Fact]) -> str:
    if not facts:
        return ''
    import time
    from datetime import datetime, timezone
    projects: dict[str, list[Fact]] = {}
    for f in facts:
        if f.project not in projects:
            projects[f.project] = []
        projects[f.project].append(f)
    now = datetime.fromtimestamp(time.time(), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    lines = ['# CORTEX Master Digest\n', f'> Snapshot Date: {now}\n', '---\n']
    for project, p_facts in sorted(projects.items()):
        lines.append(f'## Domain: {project.upper()}\n')
        types: dict[str, list[Fact]] = {}
        for f in p_facts:
            t = f.fact_type or 'general'
            if t not in types:
                types[t] = []
            types[t].append(f)
        for ftype, t_facts in sorted(types.items()):
            lines.append(f'### {ftype.capitalize()}\n')
            for f in t_facts:
                tags_str = f" [tags: {', '.join(f.tags)}]" if f.tags else ''
                lines.append(f'- **{f.content}** (Confidence: {f.confidence}){tags_str}\n')
        lines.append('\n')
    return ''.join(lines)

def _export_json(facts: list[Fact]) -> str:
    return json.dumps([f.to_dict() for f in facts], indent=2, ensure_ascii=False)

def _export_csv(facts: list[Fact]) -> str:
    if not facts:
        return ''
    output = io.StringIO()
    fieldnames = ['id', 'project', 'content', 'fact_type', 'tags', 'confidence', 'valid_from', 'valid_until', 'source']
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for f in facts:
        d = f.to_dict()
        d['tags'] = ';'.join(d.get('tags', []))
        writer.writerow({k: d.get(k, '') for k in fieldnames})
    return output.getvalue()

def _export_jsonl(facts: list[Fact]) -> str:
    lines = [json.dumps(f.to_dict(), ensure_ascii=False) for f in facts]
    return '\n'.join(lines)