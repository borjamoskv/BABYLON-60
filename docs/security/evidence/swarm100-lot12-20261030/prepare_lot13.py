"""Prepare the next thirty open findings without applying production changes."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
NEXT = HERE.parent / "swarm100-lot13-plan-20261030"
ACCEPTANCE = {
"C0045": "Longitudes 0–3 y fronteras SIMD sin underflow ni lectura fuera del buffer; comparar con referencia escalar.",
"C0046": "Intención durable recuperable antes de cuarentena; fallos por etapa conservan o recuperan el archivo.",
"C0052": "Dos instancias comparten presupuesto vigente y rechazan excedente bajo intercalado controlado.",
"C0053": "Recuperación de recibos restaura el cargo exactamente una vez tras reinicio, sin presupuesto gratuito.",
"C0054": "Ningún texto o prefijo obtiene verificación sin firma y ancla válida; ausencia de checker rechaza.",
"C0091": "Longitud del sobre validada antes del slice; entradas truncadas y límites devuelven rechazo sin panic.",
"C0107": "Mutar statement o justification invalida verificación; compatibilidad y alcance del hash explícitos.",
"C0201": "Prueba ligada a modelo/entrada/salida e inferencia realmente evaluada; sin puente comprobado no certificar.",
"C0202": "Setup reproducible públicamente no habilita producción; exigir parámetros confiables o bloquear capacidad.",
"C0214": "Slots de pila nunca exceden marco reservado; entradas en frontera y exceso rechazan o dimensionan de forma segura.",
"C0326": "Overflow de operaciones VM produce parada tipada y no panic, tanto debug como release.",
"C0335": "División por cero y MIN/-1 producen halt crítico definido, sin panic.",
"C0336": "HEALTHY solo tras inspeccionar el ledger solicitado; ausente/corrupto/no ejecutado no aprueba.",
"C0341": "Ancla externa obligatoria; auto-firma del manifiesto, clave ajena y campos alterados rechazan.",
"C0349": "Exclusión cubre leer/modificar/append entre escritores e instancias, sin pérdida ni bifurcación.",
"C0350": "Confirmación solo después de sincronizar; errores de escritura/sync observables sin falso éxito.",
"C0381": "Exportaciones forenses exclusivas no sustituyen evidencia anterior, incluso con reloj fijo y concurrencia.",
"C0393": "Postcondiciones verificadas requieren observación independiente del efecto; simulación no equivale a verificación.",
"C0442": "Reducción F60 preserva el valor para factores parciales de base, contra referencia racional.",
"C0443": "División conserva ambas escalas del denominador/numerador; cero, signo y extremos definidos.",
"C0481": "Truncar presentación no modifica cursor GGUF; arrays largos seguidos por campos se parsean íntegros.",
"C0493": "Campos del ledger se insertan como texto escapado; payload HTML no crea nodos ni ejecuta código.",
"C0502": "Rechazar buffers menores que stride antes de FFI; extremos y formato sin lecturas fuera de límites.",
"C0526": "Completion devuelve inferencia observada o error no disponible; nunca texto prefabricado presentado como modelo.",
"C0565": "Compilador del contenedor satisface rust-version de manifests; comprobación locked y build aislado cuando sea viable.",
"C0001": "Timeout/error/envío cancelado retiran futuros pendientes; respuesta tardía y cierre no filtran recursos.",
"C0002": "Navegaciones sucesivas retiran listeners propios; errores/cancelación no acumulan callbacks.",
"C0003": "Timeout de lanzamiento termina y espera exclusivamente al proceso hijo de fixture creado por esa llamada.",
"C0004": "PoC no anuncia éxito al vencer plazo; cuenta/resultado del DAG observados determinan salida.",
"C0005": "Verificador de ejecución detecta archivos no versionados dentro de su contrato, sin ignorar silenciosamente cambios.",
}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    round3 = HERE.parent / "swarm100-round3-20261028"
    excluded = {r["candidate_id"] for r in read(HERE / "execution-contract.json")["selection"]}
    queue = read(round3 / "remediation-queue.json")
    rows = [r for r in queue if r["remediation_state"] == "OPEN" and r["decision"] != "DUPLICATE" and r["candidate_id"] not in excluded][:30]
    assert len(rows) == len({r["candidate_id"] for r in rows}) == 30
    records = {r["original"]["candidate_id"]: r for r in read(round3 / "registry.json")["records"]}
    selected = []
    for row in rows:
        current = records[row["candidate_id"]]["current"]
        selected.append({**row, "rationale": current["rationale"], "source_checks": current["source_checks"],
                         "registry_review_sha256": current.get("current_source_sha256"),
                         "source_sha256": sha(ROOT / row["path"]),
                         "acceptance": ACCEPTANCE[row["candidate_id"].split("-")[-1]]})
    NEXT.mkdir(exist_ok=True)
    (NEXT / "selection-30.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n")
    counts = dict(Counter(r["severity"] for r in rows))
    sources = {r["path"]: r["source_sha256"] for r in selected}
    primary_source_count = len(sources)
    surfaces = [dict(r, source_sha256=sha(ROOT / r["path"])) for r in queue
                if r.get("counting_unit") == "SEPARATE_DUPLICATE_SURFACE" and r["remediation_state"] == "OPEN"]
    (NEXT / "duplicate-surface-obligations.json").write_text(json.dumps(surfaces, ensure_ascii=False, indent=2) + "\n")
    sources.update({r["path"]: r["source_sha256"] for r in surfaces})
    (NEXT / "plan-validation.json").write_text(json.dumps({"status": "PLAN_ONLY", "selected_unique": 30,
        "severity": counts, "source_files": len(sources), "primary_source_files": primary_source_count,
        "additional_duplicate_surfaces": len(surfaces), "all_open": True, "production_edits": False,
        "source_sha256": sources, "registry_summary_sha256": sha(round3 / "registry-summary.json"),
        "limits": "Selection retains historical findings; reconfirm source, caller contracts and red reproductions before any next-lot edit."}, indent=2) + "\n")
    lines = ["# Lote 13 propuesto: 30 hallazgos — 30/10/2026", "",
        f"Estado: **solo planificación; sin aplicar**. Son 30 hallazgos únicos OPEN: {counts.get('P1', 0)} P1 y {counts.get('P2', 0)} P2, en {primary_source_count} fuentes principales, más {len(surfaces)} copia secundaria pendiente ({len(sources)} fuentes previstas en total).", "",
        "Selección por severidad y orden de la cola tras el Lote 12. Las rutas repetidas se tratarán juntas. No se incluyen duplicados ni mitigaciones para completar el cupo.", "",
        "La [selección con hashes](evidence/swarm100-lot13-plan-20261030/selection-30.json) conserva el dictamen histórico y el hash observado ahora. No constituye reproducción ni reevaluación del código cambiado por otros trabajos. El [control del plan](evidence/swarm100-lot13-plan-20261030/plan-validation.json) registra los 30 IDs, sus fuentes y el resumen del inventario.", "",
        "## Alcance y aceptación", "", "| ID | Prioridad | Fuente prevista | Aceptación antes del cierre |", "| --- | --- | --- | --- |"]
    lines += [f"| {r['candidate_id'].split('-')[-1]} | {r['severity']} | `{r['path']}` | {r['acceptance']} |" for r in selected]
    lines += ["", "## Copia pendiente sin incrementar el cupo único", "",
        "La [obligación de superficie duplicada](evidence/swarm100-lot13-plan-20261030/duplicate-surface-obligations.json) incorpora C0461 (P1), copia secundaria de C0103. Su archivo quedó fuera de las 29 fuentes del Lote 12 y sigue OPEN. Se incluye como reparación de una superficie del mismo hallazgo, sin contarla como un hallazgo único adicional.", ""]
    lines += [f"- `{r['path']}`: reproducir inyección en fixture antes de editar y aplicar argumentos literales sin shell, conservando controles positivos y de URL/directorio. Hash previo registrado; no heredar el cierre del archivo canónico." for r in surfaces]
    lines += ["", "## Protocolo de ejecución futura", "",
        "Reconfirmar hashes, estado OPEN, grafo y consumidores antes de editar. Reproducir cada fallo primero con entradas propias; conservar red/green, comandos, fuentes y revisión independiente. Si el código actual ya cambió, readjudicar con evidencia y no aplicar un parche histórico a ciegas.", "",
        "Agrupar por dependencia: memoria/FFI y buffers; intención/ledger/presupuesto; firmas/pruebas y confianza; aritmética; inferencia/parser/UI; contenedor/CDP/verificadores. Propietarios exclusivos por archivo y revisión de intercalados/consumidores compartidos.", "",
        "Solo fixtures temporales, SQLite/ledgers propios, procesos hijos identificados y claves software sintéticas. No datos del operador, hardware, proveedores, despliegues, publicación ni mutaciones del Git real. Pruebas de bloqueo/denegación no acreditan una capacidad criptográfica o de inferencia inexistente. Si falta el checker o la correspondencia de la prueba, bloquear promoción y mantener MITIGATED/NO_VERIFICADO según evidencia.", "",
        "Aplican los [contratos por ámbito](../03_guides/agent_contracts.md). Rust: cargo check o tests dirigidos con --locked y perfiles relevantes; C/FFI: casos de frontera y comprobaciones de memoria disponibles; Python: uv --locked, Ruff/MyPy; shell: sintaxis y fixtures; HUD: Playwright con payloads de fixture y observación del DOM. CI remoto solo si se evalúa. No dependencias ni lockfiles sobre árbol sucio; necesidades de Docker/build se prepararán aisladamente sin desplegar.", "",
        "Reconciliar solo IDs con evidencia actual; conservar historia, duplicados y límites. Preparar el siguiente lote de 30 sin aplicarlo. **Este plan no autoriza su ejecución automática al finalizar el Lote 12.**", ""]
    target = ROOT / "docs/security/PLAN_SWARM100_LOTE13_2026-10-30.md"
    target.write_text("\n".join(lines))
    print(json.dumps({"plan": str(target.relative_to(ROOT)), "selected": len(rows), "severity": counts, "sources": len(sources)}))


if __name__ == "__main__":
    main()
