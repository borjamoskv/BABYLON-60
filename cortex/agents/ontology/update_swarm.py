# C5-REAL: Update Swarm YAML
import yaml
import sys
import os

yaml_file: str = '$CORTEX_ROOT/borjamoskv/Teorema-Robinson-Moskv/cortex/agents/ontology/02_INVARIANTES_TERMODINAMICAS.yaml'

def main() -> None:
    assert os.path.exists(yaml_file), f"YAML file does not exist: {yaml_file}"
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data: dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
        sys.stderr.write(f"Error C5-REAL parseando YAML (YAMLError): {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Error I/O: {e}\n")
        sys.exit(1)

    new_inv: dict[str, str] = {
        'id': 'INV-101',
        'invariante': 'Swarm Consensus (N=3)',
        'lógica___principio': 'La estructura jerárquica es entropía pura de comunicación (O(n^2)). El capital se evapora en sincronización, no en ejecución. Sustituir gerencia por protocolos de consenso deterministas.',
        'implicación_operacional': 'Cada nodo (humano o agente C5-REAL) tiene poder de commit y asume responsabilidad absoluta del fallo (Git Sentinel). N=3 requerido para BFT.',
        'condición_de_borde': 'Sincronización gerencial no determinista (Anergía).',
        'métrica_falsable': 'Hash de consenso multo-nodo validado == Git Sentinel hash.'
    }

    assert 'entities' in data, "YAML data must contain 'entities' key"
    data['entities'].append(new_inv)

    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    sys.stdout.write("Updated yaml\n")

if __name__ == '__main__':
    main()
