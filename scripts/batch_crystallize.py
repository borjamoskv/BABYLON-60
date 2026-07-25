import hashlib
import json
import os
import sys
import time


def batch_crystallize(matrices: list[dict[str, str]]) -> None:
    ontology_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cortex', 'ontology')
    os.makedirs(ontology_dir, exist_ok=True)
    hashes = []
    for i, matrix in enumerate(matrices):
        concept = matrix.get('concept', f'unnamed_matrix_{i}')
        content = matrix.get('content', '')
        path = os.path.join(ontology_dir, f'{concept}.yaml')
        taint_payload = f'borjamoskv:batch_crystallize:{time.time()}:{content}'
        taint = hashlib.sha3_256(taint_payload.encode('utf-8')).hexdigest()
        yaml_content = f'{content}\nCORTEX_TAINT: taint:borjamoskv:batch_crystallize:{time.time()}:{taint}\n'
        with open(path, 'w') as f:
            f.write(yaml_content)
        hashes.append((concept, taint))
    print('[+] BATCH CRYSTALLIZE COMPLETADO')
    for concept, h in hashes:
        print(f'    - {concept} -> {h}')
if __name__ == '__main__':
    if len(sys.argv) > 1:
        payload = sys.argv[1]
        try:
            matrices = json.loads(payload)
            batch_crystallize(matrices)
        except json.JSONDecodeError:
            print('[-] FATAL: Payload de matrices no es JSON valido.')
            sys.exit(1)
    else:
        print('[-] FATAL: No se proporcionaron matrices.')
        sys.exit(1)