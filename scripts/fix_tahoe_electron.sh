#!/bin/bash
# fix_tahoe_electron.sh  v4
# Diagnostico + mitigacion para apps Electron/Chromium que mueren en macOS Tahoe 26.5.x
#
#   bash fix_tahoe_electron.sh --diag     -> SOLO diagnostica, no toca nada  (EMPIEZA AQUI)
#   bash fix_tahoe_electron.sh            -> diagnostica y aplica mitigacion
#   bash fix_tahoe_electron.sh --watch    -> vigila y captura el estado EN EL INSTANTE de la muerte
#   bash fix_tahoe_electron.sh --verify   -> comprueba si la mitigacion esta activa
#   bash fix_tahoe_electron.sh --undo     -> revierte la mitigacion (recupera GPU)
#
# No destructivo: backup .bak.<timestamp> antes de escribir. Idempotente.
set -uo pipefail

MODE="apply"
case "${1:-}" in
  --diag|--dry-run) MODE="diag" ;;
  --undo|--revert)  MODE="undo" ;;
  --watch)          MODE="watch" ;;
  --verify)         MODE="verify" ;;
  -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
esac

REPORT="$HOME/Desktop/tahoe_electron_report.txt"
WATCHLOG="$HOME/Desktop/tahoe_watchdog.log"
say() { printf "\n\033[1m== %s ==\033[0m\n" "$1"; }
ok()  { printf "  \033[32m[ok]\033[0m %s\n" "$1"; }
warn(){ printf "  \033[33m[!]\033[0m %s\n" "$1"; }
bad() { printf "  \033[31m[X]\033[0m %s\n" "$1"; }

command -v python3 >/dev/null 2>&1 || { bad "Falta python3: xcode-select --install"; exit 1; }

# ===========================================================================
if [ "$MODE" = "verify" ]; then
  say "Estado de la mitigacion"
  v="$(defaults read com.google.Chrome HardwareAccelerationModeEnabled 2>/dev/null)"
  [ "$v" = "0" ] && ok "Chrome: GPU desactivada por politica (comprueba en chrome://gpu)" \
                 || warn "Chrome: sin politica activa (valor: ${v:-ninguno})"
  for f in "$HOME/Library/Application Support/Code/argv.json" \
           "$HOME/Library/Application Support/Code - Insiders/argv.json" \
           "$HOME/Library/Application Support/Cursor/argv.json"; do
    [ -f "$f" ] || continue
    if grep -q '"disable-hardware-acceleration"[[:space:]]*:[[:space:]]*true' "$f" 2>/dev/null; then
      ok "$(basename "$(dirname "$f")"): GPU desactivada"
    else
      warn "$(basename "$(dirname "$f")"): GPU activa"
    fi
  done
  exit 0
fi

# ===========================================================================
if [ "$MODE" = "undo" ]; then
  say "REVERTIR mitigacion"
  defaults delete com.google.Chrome HardwareAccelerationModeEnabled 2>/dev/null \
    && ok "Chrome: politica eliminada" || ok "Chrome: no habia politica"
  for f in "$HOME/Library/Application Support/Code/argv.json" \
           "$HOME/Library/Application Support/Code - Insiders/argv.json" \
           "$HOME/Library/Application Support/Cursor/argv.json"; do
    [ -f "$f" ] || continue
    cp "$f" "$f.bak.$(date +%s)" 2>/dev/null
    python3 - "$f" <<'PY'
import json,re,sys
p=sys.argv[1]; raw=open(p,encoding="utf-8").read()
s=re.sub(r'("(?:[^"\\]|\\.)*")|//[^\n]*',lambda m:m.group(1) or '',raw)
s=re.sub(r',(\s*[}\]])',r'\1',s)
try: d=json.loads(s) if s.strip() else {}
except Exception: sys.exit(0)
if d.pop("disable-hardware-acceleration",None) is not None:
    open(p,"w",encoding="utf-8").write(json.dumps(d,indent=2)+"\n"); print("  [ok] revertido:",p)
PY
  done
  for v in ELECTRON_DISABLE_GPU ELECTRON_DISABLE_HW_ACCELERATION; do launchctl unsetenv "$v" 2>/dev/null; done
  echo; ok "Hecho. Reinicia Chrome y VS Code para recuperar la GPU."
  exit 0
fi

# ===========================================================================
if [ "$MODE" = "watch" ]; then
  say "WATCHDOG — captura el estado en el instante de la muerte"
  echo "  Vigilando Chrome / Code / Cursor / Electron cada 5 s."
  echo "  Log: $WATCHLOG"
  echo "  Dejalo corriendo en esta ventana y usa el Mac normal. Ctrl-C para parar."
  echo "  Cuando una app muera, aqui quedara registrado CUANTA memoria habia en ese momento,"
  echo "  que es lo que separa 'jetsam por memoria' de 'muerte por WindowServer/GPU'."
  {
    echo "=== watchdog iniciado $(date '+%F %T') ==="
    sysctl -n hw.memsize | awk '{printf "RAM total: %.0f GB\n", $1/1073741824}'
  } >> "$WATCHLOG"
  prev=""
  trap 'echo; ok "Watchdog detenido. Log: $WATCHLOG"; exit 0' INT
  while true; do
    # solo procesos PRINCIPALES: los "Helper" (renderers) mueren y renacen sin parar
    # y generarian falsos positivos constantes.
    cur="$(pgrep -fl 'Google Chrome$|Electron$|Cursor$|/Code$|Slack$|Discord$|Notion$|Figma$|Obsidian$|Spotify$' 2>/dev/null | awk '{print $1}' | sort -n | tr '\n' ' ')"
    if [ -n "$prev" ]; then
      for pid in $prev; do
        case " $cur " in
          *" $pid "*) ;;
          *)
            ts="$(date '+%F %T')"
            {
              echo "--- MUERTE detectada $ts  pid=$pid"
              echo "    presion de memoria:"; memory_pressure 2>/dev/null | tail -2 | sed 's/^/      /'
              echo "    swap: $(sysctl -n vm.swapusage 2>/dev/null)"
              echo "    libre(paginas): $(vm_stat 2>/dev/null | awk '/free/{print $3}')"
              echo "    top RSS:"; ps -Ao rss,comm -r 2>/dev/null | head -4 | sed 's/^/      /'
              echo "    ips nuevos en los ultimos 60s:"
              find "$HOME/Library/Logs/DiagnosticReports" /Library/Logs/DiagnosticReports \
                   -name '*.ips' -mtime -60s 2>/dev/null | sed 's/^/      /' | head -5
            } >> "$WATCHLOG"
            printf "  \033[31m[MUERTE]\033[0m %s pid=%s -> registrado en el log\n" "$ts" "$pid"
            ;;
        esac
      done
    fi
    prev="$cur"
    sleep 5
  done
fi

# tee via sustitucion de proceso: sin este trap, el shell puede salir antes de que
# tee vacie su buffer y el informe en disco sale truncado por la cola.
exec > >(tee "$REPORT") 2>&1
trap 'sleep 0.4' EXIT

# ===========================================================================
say "0. Entorno"
sw_vers 2>/dev/null | sed 's/^/  /'
echo "  Chip:   $(sysctl -n machdep.cpu.brand_string 2>/dev/null)"
echo "  RAM:    $(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 )) GB"
echo "  Uptime: $(uptime | sed 's/^ *//')"

# ===========================================================================
say "1. Informes de crash (usuario + SISTEMA: los jetsam viven en /Library)"
python3 <<'PY'
import os, json, glob, collections
DIRS = [os.path.expanduser("~/Library/Logs/DiagnosticReports"),
        "/Library/Logs/DiagnosticReports"]
pairs = []
for d in DIRS:
    try:
        for f in glob.glob(os.path.join(d, "*.ips")):
            try: pairs.append((os.path.getmtime(f), f))   # el fichero puede desaparecer entre glob y stat
            except OSError: pass
    except Exception: pass
files = [f for _, f in sorted(pairs, reverse=True)[:60]]

tally = collections.Counter(); crashes = []; jetsams = []; otros = []; unreadable = 0
for f in files:
    try:
        raw = open(f, encoding="utf-8", errors="replace").read()
        head, _, body = raw.partition("\n")
        h = json.loads(head)
        try: b = json.loads(body)
        except Exception: b = {}
    except PermissionError:
        unreadable += 1; continue
    except Exception:
        unreadable += 1; continue
    base  = os.path.basename(f)
    name  = b.get("procName") or h.get("app_name") or base
    btype = str(h.get("bug_type",""))
    exc, term = (b.get("exception") or {}), (b.get("termination") or {})
    etype, sig = exc.get("type",""), exc.get("signal","")
    ind, byp   = term.get("indicator",""), term.get("byProc","")
    rec = dict(mt=os.path.getmtime(f), name=name, etype=etype, sig=sig, ind=ind,
               byp=byp, osv=h.get("os_version",""), ts=h.get("timestamp",""),
               sysdir=f.startswith("/Library"))
    if btype == "298" or "Jetsam" in base:
        # en jetsam el proceso relevante suele ser largestProcess
        rec["name"] = b.get("largestProcess") or name
        jetsams.append(rec); tally[(rec["name"], "JETSAM (presion de memoria)", "")] += 1
    elif etype or sig or ind or byp:
        crashes.append(rec); tally[(name, f"{etype} {sig}".strip(), f"{ind}{' <- '+byp if byp else ''}")] += 1
    else:
        # .ips sin firma: cuelgues (spin), informes de log, wakeups... no son crashes.
        # Meterlos con los crashes hacia que el "ultimo crash" saliera con campos vacios.
        otros.append(rec)

n_ok = len(crashes) + len(jetsams) + len(otros)
print(f"  {n_ok} informes legibles de {len(files)} encontrados" + (f"  ({unreadable} sin permiso/ilegibles)" if unreadable else ""))
if not crashes and not jetsams:
    print("  [!] Cero informes con firma utilizable. Eso YA es un dato: un SIGKILL externo")
    print("      (jetsam o WindowServer) mata el proceso sin volcado. Usa --watch.")
else:
    print("\n  PATRON (proceso / excepcion / quien lo mata):")
    for (n,e,t), c in tally.most_common(12):
        print(f"    {c:>3}x  {n:<34} {e:<26} {t}")
    if otros:
        print(f"    ({len(otros)} informe(s) sin firma de excepcion: cuelgues/spin/log, no son crashes)")
    if crashes:
        r = crashes[0]
        print("\n  ULTIMO CRASH con volcado:")
        print(f"    proceso   : {r['name']}")
        print(f"    excepcion : {(r['etype']+' '+r['sig']).strip() or '(sin campo exception)'}")
        print(f"    terminado : {r['ind'] or '(n/d)'}" + (f"   por {r['byp']}" if r['byp'] else ""))
        print(f"    os        : {r['osv']}   {r['ts']}")
    if jetsams:
        print(f"\n  JETSAM: {len(jetsams)} informe(s). Mas reciente: {jetsams[0]['ts']}")

    sigs = " ".join(f"{r['etype']} {r['sig']} {r['ind']} {r['byp']}" for r in crashes)
    print("\n  >>> VEREDICTO:")
    hit = False
    if jetsams:
        print("    * JETSAM presente -> macOS mata apps por PRESION DE MEMORIA. NO es el bug de")
        print("      _cornerMask y desactivar la GPU no lo arregla (incluso la empeora un poco).")
        hit = True
    if "EXC_BREAKPOINT" in sigs or "SIGTRAP" in sigs:
        print("    * EXC_BREAKPOINT/SIGTRAP -> bug de sandbox en builds Mac App Store (electron#49522).")
        print("      Solucion: instalar la build directa del fabricante, no la del MAS.")
        hit = True
    if "SIGKILL" in sigs or "Killed: 9" in sigs:
        who = sorted({r['byp'] for r in crashes if r['byp']})
        print(f"    * SIGKILL externo{' (por: '+', '.join(who)+')' if who else ''} -> via WindowServer/GPU.")
        print("      La mitigacion de las secciones 6-7 es la correcta.")
        hit = True
    if "SIGSEGV" in sigs or "EXC_BAD_ACCESS" in sigs:
        print("    * SIGSEGV/EXC_BAD_ACCESS -> fallo interno del proceso. Si el frame superior es")
        print("      GPU/Skia/Metal la mitigacion aplica; si no, es bug de la app concreta.")
        hit = True
    if not hit:
        print("    * Firma no reconocida: probablemente NO es este bug. Revisa el .ips entero")
        print("      antes de desactivar la GPU.")
PY

# ===========================================================================
say "2. Linea temporal: fue de verdad la actualizacion? (tarda ~20s)"
python3 - <<'PY'
import os, glob, json, time, subprocess, datetime
def fmt(t): return time.strftime("%F %T", time.localtime(t))

fs = []
for d in (os.path.expanduser("~/Library/Logs/DiagnosticReports"), "/Library/Logs/DiagnosticReports"):
    for f in glob.glob(os.path.join(d, "*.ips")):
        try: fs.append(os.path.getmtime(f))
        except OSError: pass
fs.sort()

inst = []
try:
    out = subprocess.run(["system_profiler","-json","SPInstallHistoryDataType"],
                         capture_output=True, text=True, timeout=120).stdout
    for it in json.loads(out).get("SPInstallHistoryDataType", []):
        nm = it.get("_name","")
        if "macOS" not in nm and "Tahoe" not in nm: continue
        ds = it.get("install_date","")
        for pat in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.datetime.strptime(ds, pat)
                if dt.tzinfo is None: dt = dt.replace(tzinfo=datetime.timezone.utc)
                inst.append((dt.timestamp(), nm, it.get("install_version","")))
                break
            except ValueError: continue
except Exception as e:
    print("    (system_profiler no disponible:", e, ")")
inst.sort()

if not fs:
    print("    Sin informes .ips. Nada que correlacionar -> usa --watch.")
else:
    print(f"    Informes .ips: {len(fs)}   primero {fmt(fs[0])}   ultimo {fmt(fs[-1])}")
if inst:
    print("    Instalaciones de macOS registradas:")
    for t, nm, v in inst[-4:]:
        print(f"      {fmt(t)}  {nm} {v}")

print("\n  >>> VEREDICTO TEMPORAL:")
if fs and inst:
    t0 = inst[-1][0]
    before = sum(1 for t in fs if t < t0)
    after  = sum(1 for t in fs if t >= t0)
    dias_b = max((t0 - fs[0]) / 86400.0, 0.0)
    dias_a = max((time.time() - t0) / 86400.0, 0.001)
    rb = before / dias_b if dias_b > 0.5 else None
    ra = after / dias_a
    print(f"    Ultima instalacion: {fmt(t0)}  ({inst[-1][1]} {inst[-1][2]})")
    print(f"    Crashes ANTES: {before}" + (f"  ({rb:.2f}/dia sobre {dias_b:.1f} dias)" if rb is not None else "  (ventana previa demasiado corta)"))
    print(f"    Crashes DESPUES: {after}  ({ra:.2f}/dia sobre {dias_a:.1f} dias)")
    if rb is None:
        print("    * No hay historico suficiente ANTES de la actualizacion para comparar tasas.")
        print("      macOS purga los .ips viejos; la ausencia de crashes previos NO prueba nada.")
    elif ra > rb * 2 and after >= 3:
        print("    * La tasa se DISPARA tras la actualizacion -> correlacion real con 26.5.x.")
    elif after == 0:
        print("    * Ningun crash posterior a la actualizacion -> las muertes no dejan volcado.")
        print("      Eso apunta a SIGKILL externo (jetsam / WindowServer). Usa --watch.")
    else:
        print("    * La tasa NO cambia de forma clara -> el problema probablemente PRECEDE a")
        print("      la actualizacion. Sospecha de una app, un agente de seguridad o la memoria.")
else:
    print("    Datos insuficientes para correlacionar.")
PY

# ===========================================================================
say "3. Agentes de seguridad / extensiones de sistema (causa frecuente e ignorada)"
echo "  Un agente de endpoint (antivirus, EDR, VPN corporativa) puede matar procesos"
echo "  o corromper su memoria. Si uno se actualizo el lunes, es sospechoso #1."
systemextensionsctl list 2>/dev/null | grep -vE "^$" | head -12 | sed 's/^/    /' || warn "systemextensionsctl no disponible"
echo "  Agentes de terceros cargados:"
ls /Library/LaunchDaemons /Library/LaunchAgents 2>/dev/null \
  | grep -viE "^(total|/Library|$)|com\.apple\." | head -12 | sed 's/^/    /' || echo "    (ninguno)"

# ===========================================================================
say "4. Muertes sin volcado: memoria / jetsam / WindowServer"
echo "  Presion de memoria actual:"
memory_pressure 2>/dev/null | tail -3 | sed 's/^/    /' || warn "memory_pressure no disponible"
echo "  Swap:"; sysctl vm.swapusage 2>/dev/null | sed 's/^/    /'
echo "  Eventos de kill/jetsam (24h, ~20s):"
log show --last 24h --style compact \
  --predicate 'eventMessage CONTAINS "jetsam" OR eventMessage CONTAINS "memorystatus" OR eventMessage CONTAINS "Killing"' \
  2>/dev/null | grep -iE "chrome|code|electron|cursor|jetsam|killing" | tail -12 | sed 's/^/    /' \
  || warn "sin resultados"
echo "  Top 5 en memoria ahora:"
ps -Ao rss,comm -r 2>/dev/null | head -6 | awk 'NR==1{print "    RSS(MB) PROCESO"; next}{printf "    %7.0f %s\n", $1/1024, $2}'

# ===========================================================================
say "5. Version de Electron por app (aqui vive el parche de _cornerMask)"
echo "  El fix upstream (electron#48376) es de oct-2025: binarios anteriores lo arrastran."
found=0
for app in /Applications/*.app /Applications/*/*.app "$HOME/Applications"/*.app; do
  fw="$app/Contents/Frameworks/Electron Framework.framework/Resources/Info.plist"
  [ -f "$fw" ] || continue
  found=1
  printf "    %-34s Electron %s\n" "$(basename "$app" .app)" \
    "$(defaults read "${fw%.plist}" CFBundleShortVersionString 2>/dev/null || echo '?')"
done
[ "$found" = "0" ] && warn "no se detectaron apps Electron en /Applications"
printf "    %-34s %s\n" "Google Chrome" "$(defaults read '/Applications/Google Chrome.app/Contents/Info' CFBundleShortVersionString 2>/dev/null || echo n/d)"

if [ "$MODE" = "diag" ]; then
  say "Modo --diag: no se ha modificado nada"
  echo "  Informe: $REPORT"
  echo "  Si no hay .ips concluyentes:  bash $0 --watch"
  exit 0
fi

# ===========================================================================
say "6. Limpiar env global heredado"
for v in ELECTRON_DISABLE_GPU ELECTRON_DISABLE_HW_ACCELERATION ELECTRON_OZONE_PLATFORM_HINT; do
  cur="$(launchctl getenv "$v" 2>/dev/null)"
  if [ -n "${cur:-}" ]; then launchctl unsetenv "$v" 2>/dev/null && ok "eliminado $v (=$cur)"; else ok "$v ausente"; fi
done
warn "launchctl setenv no persiste ni lo heredan las apps del Dock: por eso no sirve de fix."

say "7. Chrome + VS Code: desactivar GPU"
defaults write com.google.Chrome HardwareAccelerationModeEnabled -bool false 2>/dev/null \
  && ok "Chrome: politica aplicada (sobrevive a reescrituras del perfil)" || bad "no se pudo aplicar"
for f in "$HOME/Library/Application Support/Code/argv.json" \
         "$HOME/Library/Application Support/Code - Insiders/argv.json" \
         "$HOME/Library/Application Support/Cursor/argv.json"; do
  [ -f "$f" ] || continue
  cp "$f" "$f.bak.$(date +%s)" 2>/dev/null
  python3 - "$f" <<'PY'
import json,re,sys,os
p=sys.argv[1]; raw=open(p,encoding="utf-8").read()
s=re.sub(r'("(?:[^"\\]|\\.)*")|//[^\n]*',lambda m:m.group(1) or '',raw)
s=re.sub(r',(\s*[}\]])',r'\1',s)
try: d=json.loads(s) if s.strip() else {}
except Exception as e: print("  [X] no parseable, intacto:",e); sys.exit(0)
d["disable-hardware-acceleration"]=True
open(p,"w",encoding="utf-8").write(json.dumps(d,indent=2)+"\n")
print("  [ok]",p.replace(os.path.expanduser("~"),"~"))
PY
done

say "8. Actualizaciones (el arreglo definitivo)"
softwareupdate --list 2>&1 | sed 's/^/  /' | head -12

say "Listo"
echo "  1. Reabre Chrome y VS Code en frio.   2. Informe: $REPORT"
echo "  3. Comprobar:  bash $0 --verify       4. Revertir:  bash $0 --undo"
