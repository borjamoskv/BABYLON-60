#!/usr/bin/env zsh

# Browser Hijack Guard
# Usage:
#   ./browser_hijack_guard.sh --audit
#   ./browser_hijack_guard.sh --fix
#
# The fix mode moves suspicious files to a timestamped backup folder next to
# this script. It avoids permanent deletion so you can inspect or restore later.

set -u

MODE="${1:---audit}"
SCRIPT_DIR="${0:A:h}"
STAMP="$(date +%Y%m%dT%H%M%S)"
BACKUP_DIR="$SCRIPT_DIR/browser-hijack-guard-backup-$STAMP"
GOOGLE_GUID="485bf7d3-0215-45af-87dc-538868000001"

BAD_IDS=(
  "edgnfbghdldhjjdomhohjgjndfelcooh" # Smart AdBlocker
  "eppiocemhmnlbhjplcgkofciiegomcon" # Urban VPN Proxy
  "flaeifplnkmoagonpbjmedjcadegiigl" # X-VPN
)

BAD_RE='search\.yahoo|yhs/search|searchtosearch|sendqueries|universal-searches|anti-phishing-protection|smart[ _-]?adblocker|urban[ _-]?vpn|falais\.com|wrd-cdn\.'

BROWSER_ROOTS=(
  "$HOME/Library/Application Support/BraveSoftware/Brave-Browser"
  "$HOME/Library/Application Support/Google/Chrome"
  "$HOME/Library/Application Support/Arc/User Data"
  "$HOME/Library/Application Support/Atlas"
)

APP_NAMES=(
  "Brave Browser"
  "Google Chrome"
  "Arc"
  "ChatGPT Atlas"
)

say() {
  print -r -- "$*"
}

section() {
  say ""
  say "== $* =="
}

have() {
  command -v "$1" >/dev/null 2>&1
}

ensure_backup_dir() {
  mkdir -p "$BACKUP_DIR/moved" "$BACKUP_DIR/copied"
}

relative_for_backup() {
  local path="$1"
  local rel="${path#$HOME/}"
  if [[ "$rel" == "$path" ]]; then
    rel="${path#/}"
  fi
  print -r -- "$rel"
}

copy_to_backup() {
  local path="$1"
  [[ -e "$path" ]] || return 0
  ensure_backup_dir
  local rel
  rel="$(relative_for_backup "$path")"
  mkdir -p "$BACKUP_DIR/copied/${rel:h}"
  cp -p "$path" "$BACKUP_DIR/copied/$rel" 2>/dev/null || cp -R "$path" "$BACKUP_DIR/copied/$rel" 2>/dev/null
}

move_to_backup() {
  local path="$1"
  [[ -e "$path" ]] || return 0
  ensure_backup_dir
  local rel dest
  rel="$(relative_for_backup "$path")"
  dest="$BACKUP_DIR/moved/$rel"
  mkdir -p "${dest:h}"
  if [[ -e "$dest" ]]; then
    dest="$dest.$STAMP"
  fi
  mv "$path" "$dest"
  say "Movido a copia: $path"
}

usage() {
  cat <<'EOF'
Uso:
  ./browser_hijack_guard.sh --audit   Revisa navegadores, buscadores y restos sospechosos.
  ./browser_hijack_guard.sh --fix     Cierra navegadores y limpia restos conocidos con backup.

Qué revisa/limpia:
  - Yahoo/searchtosearch/sendqueries/universal-searches en bases Web Data e History.
  - Extensiones conocidas: Smart AdBlocker, Urban VPN Proxy, X-VPN.
  - Preferencias de Chromium y proveedor por defecto, intentando dejar Google.
  - Estado de sesiones/local storage con URLs sospechosas.
  - Proxy, DNS y buscador de Safari como señales de auditoría.
EOF
}

profile_dirs() {
  local root="$1"
  [[ -d "$root" ]] || return 0
  find "$root" -maxdepth 2 \( \
    -name "Default" -o \
    -name "Profile *" -o \
    -name "Guest Profile" -o \
    -name "System Profile" \
  \) -type d 2>/dev/null
}

audit_web_data() {
  section "Buscadores Chromium"
  if ! have sqlite3; then
    say "sqlite3 no está disponible; salto esta parte."
    return
  fi

  local found=0 db rows
  for root in "${BROWSER_ROOTS[@]}"; do
    [[ -d "$root" ]] || continue
    while IFS= read -r db; do
      [[ -f "$db" ]] || continue
      rows="$(sqlite3 "$db" "select short_name || ' | ' || keyword || ' | ' || coalesce(url,'') from keywords where lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%yahoo%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%searchtosearch%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%sendqueries%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%universal-searches%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%anti-phishing-protection%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%urban%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%falais%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%smart.adblock%';" 2>/dev/null || true)"
      if [[ -n "$rows" ]]; then
        found=1
        say "Sospechoso en: $db"
        print -r -- "$rows"
      fi
    done < <(find "$root" -name "Web Data" -type f 2>/dev/null)
  done

  if [[ "$found" -eq 0 ]]; then
    say "OK: no veo Yahoo ni motores sospechosos en Web Data."
  fi
}

audit_bad_extension_paths() {
  section "Extensiones sospechosas"
  local id root hits found=0
  for root in "${BROWSER_ROOTS[@]}"; do
    [[ -d "$root" ]] || continue
    for id in "${BAD_IDS[@]}"; do
      hits="$(find "$root" \( \
        -path "*/Extensions/$id" -o \
        -path "*/Local Extension Settings/$id" -o \
        -path "*/Sync Extension Settings/$id" -o \
        -path "*/Managed Extension Settings/$id" -o \
        -path "*/IndexedDB/chrome-extension_${id}_0.indexeddb*" \
      \) -prune -print 2>/dev/null)"
      if [[ -n "$hits" ]]; then
        found=1
        print -r -- "$hits"
      fi
    done
  done
  if [[ "$found" -eq 0 ]]; then
    say "OK: no veo instaladas Smart AdBlocker, Urban VPN Proxy ni X-VPN."
  fi
}

audit_state_strings() {
  section "Restos en sesiones y estado"
  if ! have rg; then
    say "ripgrep no está disponible; salto esta parte."
    return
  fi

  local found=0 root hits
  for root in "${BROWSER_ROOTS[@]}"; do
    [[ -d "$root" ]] || continue
    hits="$(find "$root" -maxdepth 4 \( \
      -name "Preferences" -o \
      -name "Secure Preferences" -o \
      -name "Network Persistent State" -o \
      -path "*/Sessions/*" -o \
      -path "*/Session Storage/*" -o \
      -path "*/Local Storage/leveldb/*" \
    \) -type f 2>/dev/null | rg -v 'browser-hijack|Backup|Cache|Code Cache|conversations-v3' | xargs rg -I -n -i "$BAD_RE" 2>/dev/null || true)"
    if [[ -n "$hits" ]]; then
      found=1
      print -r -- "$hits" | head -80
    fi
  done

  if [[ -d "$HOME/Library/Application Support/Arc" ]]; then
    hits="$(find "$HOME/Library/Application Support/Arc" -maxdepth 2 \( \
      -name "StorableSidebar*.json" -o \
      -name "StorableSessionRestorationData*.json" -o \
      -name "StorableWindows*.json" \
    \) -type f 2>/dev/null | xargs rg -I -n -i "$BAD_RE" 2>/dev/null || true)"
    if [[ -n "$hits" ]]; then
      found=1
      print -r -- "$hits" | head -80
    fi
  fi

  if [[ "$found" -eq 0 ]]; then
    say "OK: no veo restos activos de Yahoo/VPN/adblocker sospechoso en estado."
  else
    say "Nota: se muestran como máximo 80 coincidencias por bloque."
  fi
}

audit_system_settings() {
  section "Sistema"
  say "Proxy web:"
  scutil --proxy 2>/dev/null | awk '/HTTPEnable|HTTPSEnable|ProxyAutoConfigEnable|SOCKSEnable|HTTPProxy|HTTPSProxy|SOCKSProxy/ {print "  " $0}' || true

  say ""
  say "DNS:"
  scutil --dns 2>/dev/null | awk '/nameserver\[[0-9]+\]/ {print "  " $0}' | sort -u || true

  say ""
  say "Safari SearchProviderIdentifier:"
  defaults read com.apple.Safari SearchProviderIdentifier 2>/dev/null || say "  No configurado o no accesible."
}

audit_running_processes() {
  section "Procesos de navegador"
  ps -axo pid=,comm= | egrep -i '/Applications/Brave Browser\.app|Brave Browser Helper|/Applications/Google Chrome\.app|Google Chrome Helper|/Applications/Arc\.app|/Applications/ChatGPT Atlas\.app|ChatGPT Atlas|/Applications/Antigravity[^/]*\.app|Antigravity Helper' | egrep -v 'egrep|browser_hijack_guard' || say "OK: no veo esos navegadores abiertos."
}

run_audit() {
  say "Auditoría iniciada: $(date)"
  audit_web_data
  audit_bad_extension_paths
  audit_state_strings
  audit_system_settings
  audit_running_processes
  say ""
  say "Auditoría terminada."
}

close_browsers() {
  section "Cerrando navegadores"
  local app
  for app in "${APP_NAMES[@]}"; do
    osascript -e "tell application \"$app\" to quit" >/dev/null 2>&1 || true
  done
  sleep 2
  pkill -TERM -f "/Applications/Brave Browser.app|Brave Browser Helper|/Applications/Google Chrome.app|Google Chrome Helper|/Applications/Arc.app|/Applications/ChatGPT Atlas.app|ChatGPT Atlas" 2>/dev/null || true
  sleep 1
}

clean_bad_extensions() {
  section "Moviendo extensiones sospechosas"
  local id root hit
  for root in "${BROWSER_ROOTS[@]}"; do
    [[ -d "$root" ]] || continue
    for id in "${BAD_IDS[@]}"; do
      while IFS= read -r hit; do
        [[ -n "$hit" ]] && move_to_backup "$hit"
      done < <(find "$root" \( \
        -path "*/Extensions/$id" -o \
        -path "*/Local Extension Settings/$id" -o \
        -path "*/Sync Extension Settings/$id" -o \
        -path "*/Managed Extension Settings/$id" -o \
        -path "*/IndexedDB/chrome-extension_${id}_0.indexeddb*" \
      \) -prune -print 2>/dev/null)
    done
  done
}

clean_sqlite_data() {
  section "Limpiando Web Data e History"
  if ! have sqlite3; then
    say "sqlite3 no está disponible; salto bases de datos."
    return
  fi

  local root db
  for root in "${BROWSER_ROOTS[@]}"; do
    [[ -d "$root" ]] || continue

    while IFS= read -r db; do
      [[ -f "$db" ]] || continue
      copy_to_backup "$db"
      sqlite3 "$db" "delete from keywords where lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%yahoo%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%searchtosearch%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%sendqueries%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%universal-searches%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%anti-phishing-protection%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%urban%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%falais%' or lower(short_name || ' ' || keyword || ' ' || coalesce(url,'')) like '%smart.adblock%';" 2>/dev/null || say "No pude escribir en: $db"
      say "Revisado Web Data: $db"
    done < <(find "$root" -name "Web Data" -type f 2>/dev/null)

    while IFS= read -r db; do
      [[ -f "$db" ]] || continue
      copy_to_backup "$db"
      sqlite3 "$db" "delete from urls where lower(url || ' ' || title) like '%search.yahoo%' or lower(url || ' ' || title) like '%yhs/search%' or lower(url || ' ' || title) like '%searchtosearch%' or lower(url || ' ' || title) like '%sendqueries%' or lower(url || ' ' || title) like '%universal-searches%' or lower(url || ' ' || title) like '%anti-phishing-protection%' or lower(url || ' ' || title) like '%urban-vpn%' or lower(url || ' ' || title) like '%falais.com%' or lower(url || ' ' || title) like '%smart.adblock%';" 2>/dev/null || say "No pude escribir en: $db"
      say "Revisado History: $db"
    done < <(find "$root" -name "History" -type f 2>/dev/null)
  done
}

clean_preferences_file() {
  local pref="$1"
  [[ -f "$pref" ]] || return 0
  [[ "$pref" == *"browser-hijack"* ]] && return 0
  copy_to_backup "$pref"

  node - "$pref" "$GOOGLE_GUID" "${BAD_IDS[@]}" <<'NODE'
const fs = require("fs");
const file = process.argv[2];
const googleGuid = process.argv[3];
const badIds = new Set(process.argv.slice(4));
const badRe = /search\.yahoo|yhs\/search|searchtosearch|sendqueries|universal-searches|anti-phishing-protection|smart[ _-]?adblocker|urban[ _-]?vpn|falais\.com|wrd-cdn\./i;

function looksBad(value) {
  if (typeof value === "string") return badRe.test(value) || badIds.has(value);
  return false;
}

function scrub(value) {
  if (Array.isArray(value)) {
    return value.map(scrub).filter((item) => item !== undefined);
  }
  if (value && typeof value === "object") {
    for (const key of Object.keys(value)) {
      if (badIds.has(key) || looksBad(key) || looksBad(value[key])) {
        delete value[key];
        continue;
      }
      const next = scrub(value[key]);
      if (next === undefined) delete value[key];
      else value[key] = next;
    }
    return value;
  }
  return looksBad(value) ? undefined : value;
}

let raw;
try {
  raw = fs.readFileSync(file, "utf8");
} catch (err) {
  process.exit(2);
}

let data;
try {
  data = JSON.parse(raw);
} catch (err) {
  process.exit(3);
}

scrub(data);

if (data.default_search_provider && typeof data.default_search_provider === "object") {
  data.default_search_provider.guid = googleGuid;
  data.default_search_provider.enabled = true;
}

if (data.search && data.search.default_search_provider) {
  data.search.default_search_provider.guid = googleGuid;
}

if (data.extensions && data.extensions.settings) {
  for (const id of badIds) delete data.extensions.settings[id];
}

fs.writeFileSync(file, JSON.stringify(data, null, 2));
NODE

  case "$?" in
    0) say "Preferencias revisadas: $pref" ;;
    2) say "No pude leer: $pref" ;;
    3) say "No es JSON válido o está bloqueado: $pref" ;;
    *) say "No pude limpiar: $pref" ;;
  esac
}

clean_preferences() {
  section "Limpiando preferencias"
  if ! have node; then
    say "Node.js no está disponible; salto Preferences/Secure Preferences."
    return
  fi

  local root pref
  for root in "${BROWSER_ROOTS[@]}"; do
    [[ -d "$root" ]] || continue
    while IFS= read -r pref; do
      clean_preferences_file "$pref"
    done < <(find "$root" \( -name "Preferences" -o -name "Secure Preferences" \) -type f 2>/dev/null)
  done
}

clean_state_files() {
  section "Moviendo estado de sesión sospechoso"
  local root file
  for root in "${BROWSER_ROOTS[@]}"; do
    [[ -d "$root" ]] || continue
    while IFS= read -r file; do
      [[ -f "$file" ]] || continue
      if rg -I -i -q "$BAD_RE" "$file" 2>/dev/null; then
        move_to_backup "$file"
      fi
    done < <(find "$root" -maxdepth 4 \( \
      -name "Network Persistent State" -o \
      -path "*/Sessions/*" -o \
      -path "*/Session Storage/*" -o \
      -path "*/Local Storage/leveldb/*" \
    \) -type f 2>/dev/null | rg -v 'browser-hijack|Backup|Cache|Code Cache|conversations-v3' || true)
  done

  if [[ -d "$HOME/Library/Application Support/Arc" ]]; then
    while IFS= read -r file; do
      [[ -f "$file" ]] || continue
      if rg -I -i -q "$BAD_RE" "$file" 2>/dev/null; then
        move_to_backup "$file"
      fi
    done < <(find "$HOME/Library/Application Support/Arc" -maxdepth 2 \( \
      -name "StorableSidebar*.json" -o \
      -name "StorableSessionRestorationData*.json" -o \
      -name "StorableWindows*.json" \
    \) -type f 2>/dev/null || true)
  fi
}

fix_safari_search() {
  section "Safari"
  defaults write com.apple.Safari SearchProviderIdentifier -string "com.google.www" 2>/dev/null || say "No pude fijar Safari a Google."
  say "Safari configurado para Google si macOS permite escribir esa preferencia."
}

run_fix() {
  say "Limpieza iniciada: $(date)"
  say "Backup: $BACKUP_DIR"
  close_browsers
  clean_bad_extensions
  clean_sqlite_data
  clean_preferences
  clean_state_files
  fix_safari_search
  say ""
  say "Limpieza terminada. Ejecuto auditoría final..."
  run_audit
  say ""
  say "Copia de seguridad creada en: $BACKUP_DIR"
}

case "$MODE" in
  --audit|"")
    run_audit
    ;;
  --fix)
    run_fix
    ;;
  --help|-h|help)
    usage
    ;;
  *)
    say "Modo no reconocido: $MODE"
    usage
    exit 2
    ;;
esac
