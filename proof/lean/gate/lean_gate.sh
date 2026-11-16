#!/usr/bin/env bash
# Lean 4 gate fail-stop para BABYLON-60/proof/lean.
# Veredicto único al final. Cualquier fallo intermedio aborta con FAIL_*; nunca degrada a PASS.
#
# Fases:
#   0  toolchain fijado
#   1  cobertura: toda fuente .lean es raíz de lean_lib/lean_exe, fixture negativo o cuarentena declarada
#   2  build explícito de TODOS los targets con --no-cache --wfail (no depende de defaultTargets)
#   3  fixtures negativos: fallan, y solo por el marcador semántico esperado
#   4  auditoría de axiomas por módulo (teoremas: propext, Quot.sound; defs: + Classical.choice)
#   5  replay del entorno en el kernel (leanchecker)
#
# Uso: gate/lean_gate.sh [evidence.json]
# Compatible con bash 3.2 (macOS): sin mapfile ni arrays asociativos; arrays vacíos protegidos.
set -euo pipefail
shopt -s nullglob

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck source=gate.conf
source gate/gate.conf
EVIDENCE="${1:-}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

die() { echo "$1" >&2; echo "VERDICT=$1"; exit 1; }
contains() { local x="$1"; shift; for y in "$@"; do [[ "$x" == "$y" ]] && return 0; done; return 1; }

# ---------- 0. toolchain ----------
[[ -f lakefile.toml ]] || die "FAIL_CONFIG: falta lakefile.toml (lakefile.lean no soportado por este gate)"
TC="$(tr -d '[:space:]' < lean-toolchain)"
[[ "$TC" == "$EXPECTED_TOOLCHAIN" ]] || die "FAIL_TOOLCHAIN: lean-toolchain=$TC esperado=$EXPECTED_TOOLCHAIN"
grep -qE '^\s*(globs|srcDir)\s*=' lakefile.toml && die "FAIL_CONFIG: globs/srcDir no soportados; el parser fallaría abierto"
echo "[0] toolchain $TC"

# ---------- 1. cobertura ----------
# Parser mínimo de lakefile.toml: [[lean_lib]] name/roots, [[lean_exe]] name/root.
# Emite "LIB <target> <root>..." / "EXE <target> <root>".
awk '
  function flush() {
    if (kind == "lean_lib") { r = (roots != "") ? roots : name; print "LIB", name, r }
    if (kind == "lean_exe") { r = (root  != "") ? root  : name; print "EXE", name, r }
    kind = ""; name = ""; roots = ""; root = ""
  }
  /^\[\[lean_lib\]\]/ { flush(); kind = "lean_lib"; next }
  /^\[\[lean_exe\]\]/ { flush(); kind = "lean_exe"; next }
  /^\[/               { flush(); next }
  kind != "" && /^[ \t]*name[ \t]*=/  { match($0, /"[^"]*"/); name = substr($0, RSTART+1, RLENGTH-2) }
  kind != "" && /^[ \t]*root[ \t]*=/  { match($0, /"[^"]*"/); root = substr($0, RSTART+1, RLENGTH-2) }
  kind != "" && /^[ \t]*roots[ \t]*=/ { s = $0; gsub(/.*\[|\].*|"|,/, " ", s); roots = s }
  END { flush() }
' lakefile.toml > "$WORK/targets.txt"

LIB_TARGETS=(); EXE_TARGETS=(); ROOTS=()
while read -r kind tgt rest; do
  # shellcheck disable=SC2206
  r=($rest)
  case "$kind" in
    LIB) LIB_TARGETS+=("$tgt"); ROOTS+=("${r[@]}") ;;
    EXE) EXE_TARGETS+=("$tgt"); ROOTS+=("${r[@]}") ;;
  esac
done < "$WORK/targets.txt"
(( ${#ROOTS[@]} > 0 )) || die "FAIL_CONFIG: 0 targets parseados (parser roto)"
# Deduplicar (un módulo puede ser raíz de lib y de exe a la vez).
UNIQ=(); for m in ${ROOTS[@]+"${ROOTS[@]}"}; do contains "$m" ${UNIQ[@]+"${UNIQ[@]}"} || UNIQ+=("$m"); done
ROOTS=("${UNIQ[@]}")

# shellcheck disable=SC2206
NEG=($NEGATIVE); QUA=($QUARANTINE)
ORPHANS=()
for f in *.lean; do
  m="${f%.lean}"
  n=0
  contains "$m" ${ROOTS[@]+"${ROOTS[@]}"} && n=$((n+1))
  contains "$m" ${NEG[@]+"${NEG[@]}"}   && n=$((n+1))
  contains "$m" ${QUA[@]+"${QUA[@]}"}   && n=$((n+1))
  (( n == 1 )) || ORPHANS+=("$m(n=$n)")
done
for m in ${ROOTS[@]+"${ROOTS[@]}"} ${NEG[@]+"${NEG[@]}"} ${QUA[@]+"${QUA[@]}"}; do
  [[ -f "$m.lean" ]] || ORPHANS+=("$m(sin_fuente)")
done
(( ${#ORPHANS[@]} == 0 )) || die "FAIL_COVERAGE: ${ORPHANS[*]}"
echo "[1] cobertura: ${#ROOTS[@]} raíces, ${#NEG[@]} negativos, ${#QUA[@]} en cuarentena"

# ---------- 2. build ----------
# Targets explícitos: defaultTargets puede omitir libs/exes y el build pasaría sin compilarlos.
lake --no-cache --wfail build ${LIB_TARGETS[@]+"${LIB_TARGETS[@]}"} ${EXE_TARGETS[@]+"${EXE_TARGETS[@]}"} > "$WORK/build.log" 2>&1 \
  || { tail -40 "$WORK/build.log" >&2; die "FAIL_BUILD"; }
if grep -qE "declaration uses 'sorry'|error:" "$WORK/build.log"; then die "FAIL_BUILD_LOG"; fi
echo "[2] build OK: ${#LIB_TARGETS[@]} libs + ${#EXE_TARGETS[@]} exes"

# ---------- 3. fixtures negativos ----------
for m in ${NEG[@]+"${NEG[@]}"}; do
  if lake env lean "$m.lean" > "$WORK/neg_$m.log" 2>&1; then
    die "FAIL_NEGATIVE_ACCEPTED: $m compila; el rechazo esperado desapareció"
  fi
  grep -qF "$NEGATIVE_MARKER" "$WORK/neg_$m.log" || die "FAIL_NEGATIVE_WRONG_REASON: $m falla sin el marcador semántico"
  # Cualquier error que no sea el marcador (imports, sintaxis, timeout) invalida el control.
  other="$(grep -E 'error' "$WORK/neg_$m.log" | grep -vF "$NEGATIVE_MARKER" || true)"
  [[ -z "$other" ]] || die "FAIL_NEGATIVE_WRONG_REASON: $m: $(echo "$other" | head -1)"
done
echo "[3] negativos: ${#NEG[@]} rechazados por la razón esperada"

# ---------- 4. axiomas ----------
AUDIT_LOG="$WORK/axioms.log"; : > "$AUDIT_LOG"
for m in ${ROOTS[@]+"${ROOTS[@]}"}; do
  sed "s/__MOD__/$m/g" gate/AxiomAudit.tpl.lean > "$WORK/aa_$m.lean"
  # Un módulo por proceso: varios exponen `main` y no son co-importables.
  if ! lake env lean "$WORK/aa_$m.lean" >> "$AUDIT_LOG" 2>&1; then
    grep -E 'FAIL_AXIOM_AUDIT|error' "$AUDIT_LOG" | tail -3 >&2
    die "FAIL_AXIOM_AUDIT: $m"
  fi
  grep -q "PASS_AXIOM_AUDIT $m " "$AUDIT_LOG" || die "FAIL_AXIOM_AUDIT: $m sin marcador PASS"
done
grep -E 'WARN_RUNTIME_GAP' "$AUDIT_LOG" >&2 || true
echo "[4] axiomas: ${#ROOTS[@]} módulos limpios"

# ---------- 5. kernel replay ----------
lake env sh -c 'command -v leanchecker' >/dev/null 2>&1 \
  || die "FAIL_KERNEL_REPLAY: leanchecker no disponible en el toolchain"
for m in ${ROOTS[@]+"${ROOTS[@]}"}; do
  lake env leanchecker "$m" > "$WORK/lc_$m.log" 2>&1 || { tail -5 "$WORK/lc_$m.log" >&2; die "FAIL_KERNEL_REPLAY: $m"; }
done
echo "[5] kernel replay: ${#ROOTS[@]} módulos"

# ---------- evidencia ----------
if [[ -n "$EVIDENCE" ]]; then
  {
    printf '{\n  "verdict": "PASS_LEAN4_BUILD_AXIOMS_COVERAGE_KERNEL",\n'
    printf '  "toolchain": "%s",\n' "$TC"
    printf '  "date_utc": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '  "manifest_sha256": "%s",\n' "$(shasum -a 256 lake-manifest.json | cut -d' ' -f1)"
    printf '  "negative": "%s",\n  "quarantine": "%s",\n' "$NEGATIVE" "$QUARANTINE"
    printf '  "not_covered": ["vacuidad de enunciados", "correspondencia modelo-Rust", "comportamiento de implemented_by/extern/partial"],\n'
    printf '  "sources": {\n'
    first=1
    for f in *.lean; do
      [[ $first == 1 ]] || printf ',\n'; first=0
      printf '    "%s": "%s"' "$f" "$(shasum -a 256 "$f" | cut -d' ' -f1)"
    done
    printf '\n  },\n  "axiom_audit": [\n'
    grep -oE 'PASS_AXIOM_AUDIT [^ ]+ decls=[0-9]+ thms=[0-9]+' "$AUDIT_LOG" | sed 's/^/    "/; s/$/",/' | sed '$ s/,$//'
    printf '  ]\n}\n'
  } > "$EVIDENCE"
  echo "evidencia: $EVIDENCE"
fi

echo "VERDICT=PASS_LEAN4_BUILD_AXIOMS_COVERAGE_KERNEL"
