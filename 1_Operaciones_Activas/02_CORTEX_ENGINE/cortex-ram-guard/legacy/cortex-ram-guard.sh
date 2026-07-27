#!/bin/zsh
# CORTEX RAM GUARD v3.0 — Sovereign Memory Pressure Daemon
set -uo pipefail

GUARD_DIR="$HOME/.cortex/ram-guard"
LOG_DIR="$GUARD_DIR/logs"
CONFIG="$GUARD_DIR/config.conf"
LOG_FILE="$LOG_DIR/ram-guard-$(date +%Y-%m-%d).log"
COOLDOWN_FILE="/tmp/cortex-ram-guard-cooldown"
STATS_FILE="$GUARD_DIR/stats-$(date +%Y-%m-%d).json"
PID_FILE="$GUARD_DIR/guard.pid"
SNAPSHOT_DIR="$GUARD_DIR/snapshots"
mkdir -p "$LOG_DIR" "$SNAPSHOT_DIR"

RAM_TOTAL_GB=$(sysctl -n hw.memsize | awk '{printf "%.0f",$1/1073741824}')

# ── DEFAULTS (overridden by config.conf) ────────────────────
YELLOW_MULT=500; ORANGE_MULT=800; RED_MULT=1200
MAX_COMET_PROCS=20; MAX_NODE_PROCS=80; MAX_RENDERER_PROCS=12
CPU_KILL_PYTHON=60; CPU_KILL_NODE=70; CPU_KILL_RENDERER=50
BUDGET_COMET_MB=1500; BUDGET_NODE_MB=2000; BUDGET_RENDERER_MB=1800; BUDGET_PYTHON_MB=1200
INTERVAL_GREEN=120; INTERVAL_YELLOW=60; INTERVAL_ORANGE=30; INTERVAL_RED=15
COOLDOWN_SECONDS=180; TREND_WINDOW=10; TREND_TOLERANCE_MB=100
STALE_RENDERER_MIN=90; PREDICT_ALERT_MIN=15; SELF_MAX_RSS_MB=50
LOG_COMPRESS_DAYS=3; LOG_DELETE_DAYS=14
NOTIFY_ENABLED=1; NOTIFY_BATCH_SECONDS=120
WHITELIST_FILE="$GUARD_DIR/whitelist.conf"

load_config() {
  [[ -f "$CONFIG" ]] && source <(grep -v '^\s*#' "$CONFIG" | grep '=' | sed 's/\s*#.*//')
}
load_config

YELLOW_SWAP_MB=$((RAM_TOTAL_GB * YELLOW_MULT))
ORANGE_SWAP_MB=$((RAM_TOTAL_GB * ORANGE_MULT))
RED_SWAP_MB=$((RAM_TOTAL_GB * RED_MULT))

# ── WHITELIST ───────────────────────────────────────────────
WHITELIST_PATTERNS=()
if [[ -f "$WHITELIST_FILE" ]]; then
  while IFS= read -r line; do
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    WHITELIST_PATTERNS+=("$line")
  done < "$WHITELIST_FILE"
fi

# ── STATE ───────────────────────────────────────────────────
typeset -a SWAP_HISTORY=()
typeset -a PENDING_NOTIFS=()
STAT_KILLS=0; STAT_PURGES=0; STAT_FREED_MB=0
CURRENT_LEVEL="GREEN"; SPOTLIGHT_THROTTLED=0
LAST_NOTIFY_TS=0

# ── CORE FUNCTIONS ──────────────────────────────────────────
log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] [$1] ${@:2}" >> "$LOG_FILE"; }

queue_notify() { PENDING_NOTIFS+=("$1"); }

flush_notifications() {
  (( ! NOTIFY_ENABLED )) && return
  local now=$(date +%s)
  (( now - LAST_NOTIFY_TS < NOTIFY_BATCH_SECONDS )) && return
  [[ ${#PENDING_NOTIFS[@]} -eq 0 ]] && return
  local summary="${#PENDING_NOTIFS[@]} acciones"
  local body="${PENDING_NOTIFS[1]}"
  (( ${#PENDING_NOTIFS[@]} > 1 )) && body="$body (+$((${#PENDING_NOTIFS[@]}-1)) más)"
  osascript -e "display notification \"$body\" with title \"⚡ RAM Guard — $summary\"" 2>/dev/null &
  PENDING_NOTIFS=()
  LAST_NOTIFY_TS=$now
}

get_swap_used_mb() {
  sysctl vm.swapusage 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="used"){gsub(/M/,"",$(i+2)); printf "%.0f",$(i+2)}}'
}

get_free_mb() {
  vm_stat 2>/dev/null | awk '/Pages free/{gsub(/\./,"",$3); printf "%.0f",$3*16384/1048576}'
}

get_pressure_level() {
  local s=$1
  if (( s >= RED_SWAP_MB )); then echo "RED"
  elif (( s >= ORANGE_SWAP_MB )); then echo "ORANGE"
  elif (( s >= YELLOW_SWAP_MB )); then echo "YELLOW"
  else echo "GREEN"; fi
}

get_interval() {
  case "$1" in
    RED) echo $INTERVAL_RED;; ORANGE) echo $INTERVAL_ORANGE;;
    YELLOW) echo $INTERVAL_YELLOW;; *) echo $INTERVAL_GREEN;;
  esac
}

is_whitelisted() {
  local cmd="$1"
  for p in "${WHITELIST_PATTERNS[@]}"; do
    [[ "$cmd" == *"$p"* ]] && return 0
  done
  return 1
}

is_in_cooldown() {
  [[ -f "$COOLDOWN_FILE" ]] || return 1
  local last=$(cat "$COOLDOWN_FILE" 2>/dev/null)
  (( $(date +%s) - last < COOLDOWN_SECONDS )) && return 0
  return 1
}

set_cooldown() { date +%s > "$COOLDOWN_FILE"; }

# ── PROCESS INFO ────────────────────────────────────────────
get_proc_rss_mb() {
  # Returns RSS in MB for a PID
  ps -p "$1" -o rss= 2>/dev/null | awk '{printf "%.0f",$1/1024}'
}

get_proc_ancestry() {
  # Returns PID→PPID chain up to 3 levels
  local pid=$1 chain="" depth=0
  while (( pid > 1 && depth < 3 )); do
    local info=$(ps -p "$pid" -o pid=,ppid=,comm= 2>/dev/null | head -1)
    [[ -z "$info" ]] && break
    local ppid=$(echo "$info" | awk '{print $2}')
    local comm=$(echo "$info" | awk '{print $3}')
    chain="${chain}${pid}(${comm})←"
    pid=$ppid
    (( depth++ ))
  done
  echo "${chain%←}"
}

get_group_rss_mb() {
  # Sum RSS for all procs matching pattern
  ps aux 2>/dev/null | grep -i "$1" | grep -v grep | awk '{sum+=$6} END {printf "%.0f",sum/1024}'
}

# ── SAFE KILL ───────────────────────────────────────────────
safe_kill() {
  local pid=$1 reason="$2"
  local cmd=$(ps -p "$pid" -o args= 2>/dev/null) || return 1
  is_whitelisted "$cmd" && return 1
  local owner=$(ps -p "$pid" -o user= 2>/dev/null | tr -d ' ') || return 1
  [[ "$owner" != "$(whoami)" ]] && return 1
  local rss=$(get_proc_rss_mb "$pid")
  local ancestry=$(get_proc_ancestry "$pid")
  kill -9 "$pid" 2>/dev/null || return 1
  log "KILL" "PID=$pid RSS=${rss}MB reason=$reason ancestry=[$ancestry] cmd=${cmd:0:80}"
  (( STAT_KILLS++ ))
  queue_notify "Kill PID=$pid (${rss}MB) $reason"
  return 0
}

# ── KILL STRATEGIES ─────────────────────────────────────────
kill_comet_debug() {
  pgrep -f "Comet.*--remote-debugging-port" 2>/dev/null | while read -r pid; do
    safe_kill "$pid" "comet-debug"
  done
}

kill_hot_procs() {
  local pattern="$1" threshold="$2" label="$3"
  ps aux 2>/dev/null | grep -i "$pattern" | grep -v grep | while read -r line; do
    local pid=$(echo "$line" | awk '{print $2}')
    local cpu=${$(echo "$line" | awk '{print $3}')%.*}
    (( cpu >= threshold )) && safe_kill "$pid" "${label}-cpu-${cpu}%"
  done
}

kill_stale_renderers() {
  ps aux 2>/dev/null | grep "Helper (Renderer)" | grep -v grep | while read -r line; do
    local pid=$(echo "$line" | awk '{print $2}')
    local cpu=${$(echo "$line" | awk '{print $3}')%.*}
    # Check elapsed time
    local etimes=$(ps -p "$pid" -o etimes= 2>/dev/null | tr -d ' ') || continue
    local elapsed_min=$((etimes / 60))
    if (( elapsed_min >= STALE_RENDERER_MIN && cpu < 5 )); then
      safe_kill "$pid" "stale-renderer-${elapsed_min}min"
    fi
  done
}

cull_by_count() {
  local pattern="$1" max_count="$2" label="$3"
  local pids=()
  while IFS= read -r pid; do pids+=("$pid"); done < <(pgrep -f "$pattern" 2>/dev/null | sort -n)
  local count=${#pids[@]}
  (( count <= max_count )) && return
  local excess=$((count - max_count))
  log "CULL" "$label: $count > max $max_count, culling $excess"
  for (( i=0; i<excess; i++ )); do
    safe_kill "${pids[$((i+1))]}" "cull-${label}"
  done
}

# ── RSS BUDGET ENFORCEMENT ──────────────────────────────────
enforce_budget() {
  local pattern="$1" budget_mb="$2" label="$3"
  (( budget_mb == 0 )) && return
  local total_rss=$(get_group_rss_mb "$pattern")
  (( total_rss <= budget_mb )) && return

  log "BUDGET" "$label: ${total_rss}MB > budget ${budget_mb}MB"
  # Kill largest RSS processes in the group until under budget
  ps aux 2>/dev/null | grep -i "$pattern" | grep -v grep | sort -k6 -rn | while read -r line; do
    (( total_rss <= budget_mb )) && break
    local pid=$(echo "$line" | awk '{print $2}')
    local rss_kb=$(echo "$line" | awk '{print $6}')
    local rss_mb=$((rss_kb / 1024))
    if safe_kill "$pid" "budget-${label}-${rss_mb}MB"; then
      total_rss=$((total_rss - rss_mb))
    fi
  done
}

# ── TREND & PREDICTION ──────────────────────────────────────
update_trend() {
  SWAP_HISTORY+=($1)
  (( ${#SWAP_HISTORY[@]} > TREND_WINDOW )) && SWAP_HISTORY=("${SWAP_HISTORY[@]:1}")
}

detect_leak() {
  (( ${#SWAP_HISTORY[@]} < TREND_WINDOW )) && return 1
  local increasing=0 prev=0
  for s in "${SWAP_HISTORY[@]}"; do
    (( s > prev + TREND_TOLERANCE_MB )) && (( increasing++ ))
    prev=$s
  done
  (( increasing >= TREND_WINDOW * 80 / 100 ))
}

predict_time_to_red() {
  # Linear extrapolation: returns minutes until RED, or -1 if stable/decreasing
  (( ${#SWAP_HISTORY[@]} < 3 )) && echo -1 && return
  local first=${SWAP_HISTORY[1]}
  local last=${SWAP_HISTORY[-1]}
  local n=${#SWAP_HISTORY[@]}
  local interval=$(get_interval "$CURRENT_LEVEL")
  local elapsed_min=$(( (n - 1) * interval / 60 ))
  (( elapsed_min == 0 )) && echo -1 && return
  local rate_per_min=$(( (last - first) / elapsed_min ))
  (( rate_per_min <= 0 )) && echo -1 && return
  local remaining=$((RED_SWAP_MB - last))
  (( remaining <= 0 )) && echo 0 && return
  echo $(( remaining / rate_per_min ))
}

# ── SNAPSHOT (periodic process state for forensics) ─────────
take_snapshot() {
  local f="$SNAPSHOT_DIR/snap-$(date +%H%M).tsv"
  echo "PID\tRSS_MB\tCPU%\tETIME\tCOMMAND" > "$f"
  ps aux -m 2>/dev/null | awk 'NR>1 && NR<=30 {printf "%s\t%.0f\t%s\t-\t%s\n",$2,$6/1024,$3,$11}' >> "$f"
  # Keep only last 24 snapshots
  ls -t "$SNAPSHOT_DIR"/snap-*.tsv 2>/dev/null | tail -n +25 | xargs rm -f 2>/dev/null
}

# ── SELF-HEALTH ─────────────────────────────────────────────
check_self_health() {
  local my_rss=$(get_proc_rss_mb $$)
  if (( my_rss > SELF_MAX_RSS_MB )); then
    log "SELF" "Guard RSS=${my_rss}MB > limit ${SELF_MAX_RSS_MB}MB — restarting"
    exec "$0" daemon  # Re-exec self to reset memory
  fi
}

# ── STATS ───────────────────────────────────────────────────
save_stats() {
  cat > "$STATS_FILE" <<EOJSON
{"date":"$(date +%Y-%m-%d)","kills":$STAT_KILLS,"purges":$STAT_PURGES,"freed_mb":$STAT_FREED_MB,"ram_gb":$RAM_TOTAL_GB,"last_swap_mb":${SWAP_USED:-0},"last_level":"$CURRENT_LEVEL","updated":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOJSON
}

load_stats() {
  [[ -f "$STATS_FILE" ]] || return
  STAT_KILLS=$(python3 -c "import json;print(json.load(open('$STATS_FILE')).get('kills',0))" 2>/dev/null || echo 0)
  STAT_PURGES=$(python3 -c "import json;print(json.load(open('$STATS_FILE')).get('purges',0))" 2>/dev/null || echo 0)
  STAT_FREED_MB=$(python3 -c "import json;print(json.load(open('$STATS_FILE')).get('freed_mb',0))" 2>/dev/null || echo 0)
}

# ── GRADUATED RESPONSE ──────────────────────────────────────
respond_yellow() {
  log "LEVEL" "YELLOW swap=${SWAP_USED}MB"
  cull_by_count "Comet" "$MAX_COMET_PROCS" "Comet"
  cull_by_count "node" "$MAX_NODE_PROCS" "Node"
  cull_by_count "Helper (Renderer)" "$MAX_RENDERER_PROCS" "Renderer"
  kill_stale_renderers
  enforce_budget "Comet" "$BUDGET_COMET_MB" "Comet"
  enforce_budget "node" "$BUDGET_NODE_MB" "Node"
}

respond_orange() {
  log "LEVEL" "ORANGE swap=${SWAP_USED}MB"
  is_in_cooldown && { log "COOLDOWN" "skip"; return; }
  respond_yellow
  kill_hot_procs "python" "$CPU_KILL_PYTHON" "python"
  kill_hot_procs "node" "$CPU_KILL_NODE" "node"
  kill_comet_debug
  enforce_budget "python" "$BUDGET_PYTHON_MB" "Python"
  enforce_budget "Helper (Renderer)" "$BUDGET_RENDERER_MB" "Renderer"
  purge 2>/dev/null && log "PURGE" "cache flushed" && (( STAT_PURGES++ ))
  set_cooldown
  queue_notify "ORANGE purge — swap ${SWAP_USED}MB"
}

respond_red() {
  log "LEVEL" "RED swap=${SWAP_USED}MB"
  is_in_cooldown && { log "COOLDOWN" "skip"; return; }
  respond_yellow
  kill_hot_procs "python" 30 "python-emerg"
  kill_hot_procs "node" 40 "node-emerg"
  kill_hot_procs "Helper (Renderer)" 20 "renderer-emerg"
  kill_comet_debug
  # Kill ALL stale renderers aggressively (>30min)
  ps aux 2>/dev/null | grep "Helper (Renderer)" | grep -v grep | while read -r line; do
    local pid=$(echo "$line" | awk '{print $2}')
    local etimes=$(ps -p "$pid" -o etimes= 2>/dev/null | tr -d ' ') || continue
    (( etimes > 1800 )) && safe_kill "$pid" "red-renderer-old"
  done
  enforce_budget "Comet" $((BUDGET_COMET_MB / 2)) "Comet-emerg"
  enforce_budget "python" $((BUDGET_PYTHON_MB / 2)) "Python-emerg"
  enforce_budget "node" $((BUDGET_NODE_MB / 2)) "Node-emerg"
  enforce_budget "Helper (Renderer)" $((BUDGET_RENDERER_MB / 2)) "Renderer-emerg"
  mdutil -i off / 2>/dev/null && log "SYSTEM" "Spotlight paused" && SPOTLIGHT_THROTTLED=1
  purge 2>/dev/null && log "PURGE" "emergency flush" && (( STAT_PURGES++ ))
  set_cooldown
  queue_notify "⚠️ RED CRÍTICO — purga emergencia — swap ${SWAP_USED}MB"
}

# ── CLI ─────────────────────────────────────────────────────
cmd_status() {
  load_config
  local swap=$(get_swap_used_mb) free=$(get_free_mb)
  local level=$(get_pressure_level "$swap")
  local pc=$(ps aux | wc -l | tr -d ' ')
  local ic=("🟢" "🟡" "🟠" "🔴")
  local li; case "$level" in GREEN) li="${ic[1]}";; YELLOW) li="${ic[2]}";; ORANGE) li="${ic[3]}";; RED) li="${ic[4]}";; esac

  echo "═══════════════════════════════════════════════"
  echo "  CORTEX RAM GUARD v3.0"
  echo "═══════════════════════════════════════════════"
  echo "  RAM:       ${RAM_TOTAL_GB}GB  │  Free: ${free}MB"
  echo "  Swap:      ${swap}MB  │  $li $level"
  echo "  Thresholds: Y=${YELLOW_SWAP_MB} O=${ORANGE_SWAP_MB} R=${RED_SWAP_MB}"
  echo "───────────────────────────────────────────────"
  printf "  %-12s %5s procs  %6sMB RSS  (budget %sMB)\n" \
    "Comet" "$(pgrep -fc Comet 2>/dev/null||echo 0)" "$(get_group_rss_mb Comet)" "$BUDGET_COMET_MB"
  printf "  %-12s %5s procs  %6sMB RSS  (budget %sMB)\n" \
    "Node" "$(pgrep -fc node 2>/dev/null||echo 0)" "$(get_group_rss_mb node)" "$BUDGET_NODE_MB"
  printf "  %-12s %5s procs  %6sMB RSS  (budget %sMB)\n" \
    "Renderer" "$(pgrep -fc 'Helper (Renderer)' 2>/dev/null||echo 0)" "$(get_group_rss_mb 'Helper (Renderer)')" "$BUDGET_RENDERER_MB"
  printf "  %-12s %5s procs  %6sMB RSS  (budget %sMB)\n" \
    "Python" "$(pgrep -fic python 2>/dev/null||echo 0)" "$(get_group_rss_mb python)" "$BUDGET_PYTHON_MB"
  echo "───────────────────────────────────────────────"
  echo "  Total procs: $pc"
  if [[ -f "$STATS_FILE" ]]; then
    echo "  Today: $(python3 -c "import json;d=json.load(open('$STATS_FILE'));print(f\"kills={d.get('kills',0)} purges={d.get('purges',0)} freed={d.get('freed_mb',0)}MB\")" 2>/dev/null)"
  fi
  echo "═══════════════════════════════════════════════"
}

cmd_purge() {
  echo "⚡ Manual purge..."
  SWAP_USED=$(get_swap_used_mb); local before=$SWAP_USED
  kill_comet_debug; kill_hot_procs "python" 30 "manual"
  kill_hot_procs "node" 40 "manual"; kill_stale_renderers
  cull_by_count "Comet" "$MAX_COMET_PROCS" "Comet"
  cull_by_count "node" "$MAX_NODE_PROCS" "Node"
  enforce_budget "Comet" "$BUDGET_COMET_MB" "Comet"
  enforce_budget "node" "$BUDGET_NODE_MB" "Node"
  enforce_budget "python" "$BUDGET_PYTHON_MB" "Python"
  purge 2>/dev/null
  sleep 3; local after=$(get_swap_used_mb)
  echo "✓ Swap: ${before}MB → ${after}MB (freed $((before-after))MB)"
}

cmd_logs() { [[ -f "$LOG_FILE" ]] && tail -50 "$LOG_FILE" || echo "No logs today."; }

cmd_stats() {
  echo "═══════════════════════════════════════════════"
  echo "  CORTEX RAM GUARD — 7-DAY HISTORY"
  echo "═══════════════════════════════════════════════"
  for i in {0..6}; do
    local d=$(date -v-${i}d +%Y-%m-%d)
    local sf="$GUARD_DIR/stats-${d}.json"
    [[ -f "$sf" ]] && printf "  %s  %s\n" "$d" "$(python3 -c "import json;d=json.load(open('$sf'));print(f\"kills={d.get('kills',0):>3} purges={d.get('purges',0):>2} freed={d.get('freed_mb',0):>5}MB level={d.get('last_level','?')}\")" 2>/dev/null)"
  done
  echo "═══════════════════════════════════════════════"
}

cmd_snapshot() { take_snapshot; echo "✓ Snapshot saved"; cat "$SNAPSHOT_DIR"/snap-$(date +%H%M).tsv; }

cmd_install() {
  local plist="$HOME/Library/LaunchAgents/com.cortex.ram-guard.plist"
  launchctl bootout gui/$(id -u) "$plist" 2>/dev/null
  cat > "$plist" <<EOPLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.cortex.ram-guard</string>
  <key>ProgramArguments</key><array><string>/bin/zsh</string><string>$GUARD_DIR/cortex-ram-guard.sh</string><string>daemon</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$LOG_DIR/stdout.log</string>
  <key>StandardErrorPath</key><string>$LOG_DIR/stderr.log</string>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>ProcessType</key><string>Background</string>
  <key>LowPriorityBackgroundIO</key><true/>
  <key>Nice</key><integer>10</integer>
</dict></plist>
EOPLIST
  launchctl bootstrap gui/$(id -u) "$plist"
  echo "✓ Installed & started"
}

cmd_uninstall() {
  launchctl bootout gui/$(id -u) "$HOME/Library/LaunchAgents/com.cortex.ram-guard.plist" 2>/dev/null
  echo "✓ Daemon stopped & unloaded"
}

# ── ENTRY ───────────────────────────────────────────────────
case "${1:-daemon}" in
  status)    cmd_status; exit 0;;
  purge)     cmd_purge; exit 0;;
  logs)      cmd_logs; exit 0;;
  stats)     cmd_stats; exit 0;;
  snapshot)  cmd_snapshot; exit 0;;
  install)   cmd_install; exit 0;;
  uninstall) cmd_uninstall; exit 0;;
  daemon)    ;;
  *) echo "Usage: ramguard {status|purge|logs|stats|snapshot|install|uninstall}"; exit 1;;
esac

# ── DAEMON LOOP ─────────────────────────────────────────────
echo $$ > "$PID_FILE"
load_stats
log "START" "v3.0 RAM=${RAM_TOTAL_GB}GB Y=${YELLOW_SWAP_MB} O=${ORANGE_SWAP_MB} R=${RED_SWAP_MB}"

CYCLE=0
while true; do
  # Reload config every 10 cycles
  (( CYCLE % 10 == 0 )) && load_config

  SWAP_USED=$(get_swap_used_mb)
  CURRENT_LEVEL=$(get_pressure_level "$SWAP_USED")
  update_trend "$SWAP_USED"

  # Snapshot every 30 cycles
  (( CYCLE % 30 == 0 )) && take_snapshot

  local swap_before=$SWAP_USED

  case "$CURRENT_LEVEL" in
    GREEN)
      (( SPOTLIGHT_THROTTLED )) && { mdutil -i on / 2>/dev/null; SPOTLIGHT_THROTTLED=0; log "SYSTEM" "Spotlight restored"; }
      ;;
    YELLOW) respond_yellow;;
    ORANGE) respond_orange;;
    RED)    respond_red;;
  esac

  sleep 3
  local swap_after=$(get_swap_used_mb)
  local freed=$((swap_before - swap_after))
  (( freed > 0 )) && STAT_FREED_MB=$((STAT_FREED_MB + freed))

  # Predictive alert
  local eta=$(predict_time_to_red)
  if (( eta >= 0 && eta < PREDICT_ALERT_MIN && CURRENT_LEVEL != "RED" )); then
    log "PREDICT" "ETA to RED: ${eta}min"
    queue_notify "⏱ RED en ~${eta}min — swap creciendo"
  fi

  # Leak detection
  detect_leak && {
    log "LEAK" "Monotonic swap growth detected across $TREND_WINDOW samples"
    ps aux -m 2>/dev/null | awk 'NR>1&&NR<=6{printf "  PID=%s RSS=%.0fMB CPU=%s CMD=%s\n",$2,$6/1024,$3,$11}' | while read -r l; do log "LEAK" "$l"; done
    queue_notify "🔍 Leak detectado — swap creciendo sin pausa"
  }

  flush_notifications
  check_self_health
  save_stats

  # Log rotation
  (( CYCLE % 60 == 0 )) && {
    find "$LOG_DIR" -name "ram-guard-*.log" -mtime +$LOG_COMPRESS_DAYS -exec gzip -q {} \; 2>/dev/null
    find "$LOG_DIR" -name "*.gz" -mtime +$LOG_DELETE_DAYS -delete 2>/dev/null
  }

  (( CYCLE++ ))
  sleep "$(get_interval "$CURRENT_LEVEL")"
done
