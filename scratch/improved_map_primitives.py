import logging
import yaml
import json
import hashlib
import math
from pathlib import Path

def calculate_entropy(text: str) -> float:
    if not text:
        return 0.0
    freqs = {}
    for char in text:
        freqs[char] = freqs.get(char, 0) + 1
    total = len(text)
    return round(sum((-(c / total) * math.log2(c / total) for c in freqs.values())), 4)

def run_improved_mapping(matrix_path: Path, article_path: Path) -> dict:
    with open(matrix_path, 'r') as f:
        matrix_data = yaml.safe_load(f)
    with open(article_path, 'r') as f:
        article_text = f.read()
    primitives = matrix_data.get('Centuria_Matrix', {}).get('Primitives', [])
    article_entropy = calculate_entropy(article_text)
    boltzmann_domains = {'SQLite_WAL', 'Thread_Lock', 'Memory_Page', 'File_Descriptor', 'BFT_Ledger'}
    mapped_records = []
    total_entropy_accumulated = 0.0
    for p in primitives:
        pid = p.get('ID')
        domain = p.get('Domain')
        desc = p.get('Description', '')
        p_entropy = calculate_entropy(desc)
        total_entropy_accumulated += p_entropy
        is_boltzmann = domain in boltzmann_domains
        thermo_vector = 'BOLTZMANN_EQUILIBRIUM' if is_boltzmann else 'PRIGOGINE_DISSIPATIVE'
        mapped_records.append({'id': pid, 'domain': domain, 'entropy': p_entropy, 'vector': thermo_vector})
    avg_p_entropy = round(total_entropy_accumulated / len(primitives), 4) if primitives else 0.0
    return {'article_metrics': {'path': str(article_path.relative_to(article_path.parents[1])), 'entropy': article_entropy, 'length_chars': len(article_text)}, 'primitives_metrics': {'total': len(primitives), 'average_entropy': avg_p_entropy, 'boltzmann_ratio': round(sum((1 for r in mapped_records if r['vector'] == 'BOLTZMANN_EQUILIBRIUM')) / len(primitives), 4)}, 'records_head': mapped_records[:10]}

def main():
    project_root = Path(__file__).resolve().parent.parent
    matrix_path = project_root / 'cortex/agents/ontology/centuria_matrix_1000.yaml'
    article_path = project_root / 'docs/substack_boltzmann_prigogine.md'
    try:
        report = run_improved_mapping(matrix_path, article_path)
        payload = json.dumps(report, sort_keys=True)
        v_hash = hashlib.sha3_256(payload.encode()).hexdigest()
        output = {'cortex_taint': f'borjamoskv:improved_thermo:{v_hash[:16]}', 'report': report, 'hash': v_hash}
        logging.info(json.dumps(output, indent=2))
    except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
        logging.info(json.dumps({'error': str(e)}))
if __name__ == '__main__':
    main()