import yaml
import sys

def main():
    yaml_path = "$CORTEX_ROOT/Downloads/matriz_1000_primitivas.yaml"
    out_md = "$CORTEX_ROOT/borjamoskv/Teorema-Robinson-Moskv/cortex/agents/ontology/06_MATRIZ_1000.md"
    
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error C5-REAL parseando YAML (YAMLError): {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error I/O: {e}", file=sys.stderr)
        sys.exit(1)
        
    with open(out_md, "w", encoding="utf-8") as out:
        out.write("<!-- Author: Borja Moskv (SYS_ID: borjamoskv) -->\n\n")
        out.write("# MATRIZ 6: MATRIZ 1000 PRIMITIVAS\n\n")
        out.write("| ID | Theory | Base | Dimension | Primitiva |\n")
        out.write("|---|---|---|---|---|\n")
        
        for t_key, t_val in data.items():
            if not isinstance(t_val, dict): continue
            base = t_val.get("base", "").replace("|", "\\|")
            dimensions = t_val.get("dimensions", {})
            
            for d_key, d_list in dimensions.items():
                for idx, prim in enumerate(d_list):
                    t_num = t_key.split('-')[0]
                    d_num = d_key.split('-')[0]
                    p_id = f"PRIM-{t_num}-{d_num}-{idx+1:02d}"
                    prim_safe = str(prim).replace("|", "\\|")
                    out.write(f"| {p_id} | {t_key} | {base} | {d_key} | {prim_safe} |\n")
                    
    print(f"[*] Escrito {out_md} con éxito.")

if __name__ == '__main__':
    main()
