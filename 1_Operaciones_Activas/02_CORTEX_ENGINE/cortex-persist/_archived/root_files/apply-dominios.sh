#!/usr/bin/env bash
# apply-dominios.sh — Fases 0-2 del plan de dominios CortexPersist en Cloudflare.
# Uso:   CF_API_TOKEN=xxx bash apply-dominios.sh           # aplica
#        CF_API_TOKEN=xxx DRY_RUN=1 bash apply-dominios.sh # solo muestra qué haría
# Requiere: curl, jq
#
# Garantías:
#  - Idempotente: re-ejecutable; nunca sobreescribe ni borra nada.
#  - No toca correo en uso (si hay MX, solo diagnostica).
#  - No redirige zonas que ya sirven contenido real.
#  - Zonas inaccesibles con el token (p. ej. otra cuenta) se saltan con aviso.

set -u
API="https://api.cloudflare.com/client/v4"
CANONICAL="cortexpersist.dev"
PARKED=("cortexpersist.org" "babylon60.com" "agents.archi")
BILLING="cortexpersist.com"
DRY_RUN="${DRY_RUN:-0}"

[ -z "${CF_API_TOKEN:-}" ] && { echo "ERROR: exporta CF_API_TOKEN"; exit 1; }
command -v jq >/dev/null || { echo "ERROR: falta jq"; exit 1; }
command -v curl >/dev/null || { echo "ERROR: falta curl"; exit 1; }

N_OK=0; N_SKIP=0; N_WARN=0; N_FAIL=0
ok()    { echo "  OK    $*"; N_OK=$((N_OK+1)); }
skip()  { echo "  SKIP  $*"; N_SKIP=$((N_SKIP+1)); }
warn()  { echo "  AVISO $*"; N_WARN=$((N_WARN+1)); }
fail()  { echo "  FALLO $*"; N_FAIL=$((N_FAIL+1)); }
plan()  { echo "  [DRY] $*"; }
info()  { echo "  INFO  $*"; }

# GETs con reintento; mutaciones sin reintento (evita duplicados si hay timeout)
cf_get() { curl -sS --retry 2 --retry-delay 1 --max-time 30 \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" "$API$1"; }
cf_mut() { # method path json
  curl -sS --max-time 30 -X "$1" \
    -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
    --data "$3" "$API$2"; }

api_errs() { jq -r '[.errors[]?.message] | join("; ")' <<<"$1"; }

# ---------- primitivas ----------

zone_lookup() { # domain -> "id status" o vacío
  cf_get "/zones?name=$1" | jq -r '.result[0] | select(.) | "\(.id) \(.status)"'
}

ensure_record() { # zid domain type name content [extra_json]
  local zid="$1" domain="$2" type="$3" name="$4" content="$5" extra="${6:-}"
  local fqdn="$name"; [ "$name" = "@" ] && fqdn="$domain"
  local n
  n=$(cf_get "/zones/$zid/dns_records?type=$type&name=$fqdn" | jq '.result | length')
  if [ "${n:-0}" -gt 0 ]; then skip "$type $fqdn (ya existe)"; return 0; fi
  if [ "$DRY_RUN" = "1" ]; then plan "CREAR $type $fqdn -> $content"; return 0; fi
  local resp okv
  resp=$(cf_mut POST "/zones/$zid/dns_records" \
    "{\"type\":\"$type\",\"name\":\"$fqdn\",\"content\":\"$content\",\"ttl\":1$extra}")
  okv=$(jq -r '.success' <<<"$resp")
  if [ "$okv" = "true" ]; then ok "$type $fqdn -> $content"
  else fail "$type $fqdn — $(api_errs "$resp")"; fi
}

has_mx()  { [ "$(cf_get "/zones/$1/dns_records?type=MX" | jq '.result | length')" -gt 0 ]; }
has_spf() { cf_get "/zones/$1/dns_records?type=TXT" \
  | jq -e '.result[]? | select(.content | test("v=spf1"))' >/dev/null 2>&1; }
has_dmarc() { [ "$(cf_get "/zones/$1/dns_records?type=TXT&name=_dmarc.$2" | jq '.result | length')" -gt 0 ]; }

# ¿La zona sirve contenido real (A/AAAA/CNAME en apex o www que no sean nuestros dummies)?
zone_serves_content() { # zid domain
  cf_get "/zones/$1/dns_records?per_page=100" | jq -e --arg d "$2" '
    [.result[] | select(
        (.type=="A" or .type=="AAAA" or .type=="CNAME")
        and (.name==$d or .name=="www."+$d)
        and (.content!="192.0.2.1" and .content!="100::" and .content!=$d)
    )] | length > 0' >/dev/null 2>&1
}

enable_dnssec() { # zid
  local st
  st=$(cf_get "/zones/$1/dnssec" | jq -r '.result.status // "unknown"')
  case "$st" in
    active) skip "DNSSEC ya activo"; return ;;
  esac
  if [ "$DRY_RUN" = "1" ]; then plan "ACTIVAR DNSSEC (estado: $st)"; return; fi
  local resp
  resp=$(cf_mut PATCH "/zones/$1/dnssec" '{"status":"active"}')
  st=$(jq -r '.result.status // "error"' <<<"$resp")
  case "$st" in
    active)   ok "DNSSEC activo" ;;
    pending*) warn "DNSSEC pendiente ($st): si el registrar no es Cloudflare, añade el DS a mano" ;;
    *)        fail "DNSSEC — $(api_errs "$resp") (activable a mano: panel DNS, 1 clic)" ;;
  esac
}

set_setting() { # zid setting value
  local cur
  cur=$(cf_get "/zones/$1/settings/$2" | jq -r '.result.value // "?"')
  if [ "$cur" = "$3" ]; then skip "$2=$3 (ya)"; return; fi
  if [ "$DRY_RUN" = "1" ]; then plan "SETTING $2: $cur -> $3"; return; fi
  local resp okv
  resp=$(cf_mut PATCH "/zones/$1/settings/$2" "{\"value\":\"$3\"}")
  okv=$(jq -r '.success' <<<"$resp")
  [ "$okv" = "true" ] && ok "$2=$3" || fail "$2 — $(api_errs "$resp")"
}

set_redirect_ruleset() { # zid domain rules_json descripcion
  local zid="$1" domain="$2" rules="$3" desc="$4" existing
  existing=$(cf_get "/zones/$zid/rulesets/phases/http_request_dynamic_redirect/entrypoint" \
    | jq '.result.rules | length' 2>/dev/null)
  if [ -n "${existing:-}" ] && [ "$existing" != "null" ] && [ "$existing" != "0" ]; then
    skip "Redirect: ya hay $existing regla(s) en $domain — no las piso"; return
  fi
  if [ "$DRY_RUN" = "1" ]; then plan "REDIRECT $desc"; return; fi
  local resp okv
  resp=$(cf_mut PUT "/zones/$zid/rulesets/phases/http_request_dynamic_redirect/entrypoint" \
    "{\"rules\":$rules}")
  okv=$(jq -r '.success' <<<"$resp")
  [ "$okv" = "true" ] && ok "Redirect: $desc" || fail "Redirect $domain — $(api_errs "$resp")"
}

parked_email_hygiene() { # zid domain
  local zid="$1" d="$2"
  if has_mx "$zid"; then
    warn "$d tiene MX — correo en uso, NO aplico higiene de aparcado"
    has_spf "$zid"      || warn "$d sin SPF — configúralo con tu proveedor"
    has_dmarc "$zid" "$d" || warn "$d sin DMARC — añade al menos p=none"
    return
  fi
  has_spf "$zid" && skip "SPF ya existe" || ensure_record "$zid" "$d" TXT "@" "v=spf1 -all"
  ensure_record "$zid" "$d" TXT "*._domainkey.$d" "v=DKIM1; p="
  has_dmarc "$zid" "$d" && skip "DMARC ya existe" \
    || ensure_record "$zid" "$d" TXT "_dmarc.$d" "v=DMARC1; p=reject; sp=reject"
  ensure_record "$zid" "$d" MX "@" "." ',"priority":0'
}

redirect_rules_to() { # host destino: todo el tráfico -> 301 canónico con path+query
  cat <<EOF
[{"action":"redirect","expression":"true","description":"301 al canonico",
  "action_parameters":{"from_value":{"status_code":301,"preserve_query_string":true,
  "target_url":{"expression":"concat(\"https://$1\", http.request.uri.path)"}}}}]
EOF
}

www_to_apex_rules() {
  cat <<EOF
[{"action":"redirect","expression":"(http.host eq \"www.$CANONICAL\")","description":"www -> apex",
  "action_parameters":{"from_value":{"status_code":301,"preserve_query_string":true,
  "target_url":{"expression":"concat(\"https://$CANONICAL\", http.request.uri.path)"}}}}]
EOF
}

harden_zone() { # zid : DNSSEC + TLS estricto + HTTPS forzado
  enable_dnssec "$1"
  set_setting "$1" ssl strict
  set_setting "$1" always_use_https on
}

# ---------- ejecución ----------

echo "== Verificando token =="
tok=$(cf_get "/user/tokens/verify" | jq -r '.result.status // "invalid"')
[ "$tok" != "active" ] && { echo "ERROR: token inválido o expirado ($tok)"; exit 1; }
echo "  token activo"
[ "$DRY_RUN" = "1" ] && echo "  MODO DRY-RUN: no se aplicará ningún cambio"

echo; echo "== Localizando zonas =="
declare -A ZID
INACCESSIBLE=()
for d in "$CANONICAL" "${PARKED[@]}" "$BILLING"; do
  read -r zid zst <<<"$(zone_lookup "$d")" || true
  if [ -z "${zid:-}" ]; then
    warn "$d no accesible con este token (¿otra cuenta / no incluida en el scope?) — la salto"
    INACCESSIBLE+=("$d")
  else
    ZID["$d"]="$zid"
    [ "$zst" != "active" ] && warn "$d en estado '$zst' (¿nameservers pendientes?)" || info "$d -> $zid"
  fi
done
[ ${#ZID[@]} -eq 0 ] && { echo "ERROR: ninguna zona accesible"; exit 1; }

if [ -n "${ZID[$CANONICAL]:-}" ]; then
  echo; echo "== $CANONICAL (canónico) =="
  zid="${ZID[$CANONICAL]}"
  harden_zone "$zid"   # .dev es HSTS-preloaded: HTTPS obligatorio, esto lo garantiza
  apex_n=$(cf_get "/zones/$zid/dns_records?name=$CANONICAL" \
    | jq '[.result[] | select(.type=="A" or .type=="AAAA" or .type=="CNAME")] | length')
  if [ "${apex_n:-0}" -eq 0 ]; then
    warn "apex sin registros: creo dummies proxied (error CF visible hasta conectar hosting)"
    ensure_record "$zid" "$CANONICAL" A "@" "192.0.2.1" ',"proxied":true'
    ensure_record "$zid" "$CANONICAL" AAAA "@" "100::" ',"proxied":true'
  else
    skip "apex ya tiene $apex_n registro(s) — no toco el hosting actual"
  fi
  ensure_record "$zid" "$CANONICAL" CNAME "www.$CANONICAL" "$CANONICAL" ',"proxied":true'
  set_redirect_ruleset "$zid" "$CANONICAL" "$(www_to_apex_rules)" "www.$CANONICAL -> apex"
  if has_mx "$zid"; then warn "$CANONICAL tiene MX — revisa SPF/DKIM/DMARC de tu proveedor"
  else parked_email_hygiene "$zid" "$CANONICAL"; fi
fi

for d in "${PARKED[@]}"; do
  [ -z "${ZID[$d]:-}" ] && continue
  echo; echo "== $d (aparcado -> redirect) =="
  zid="${ZID[$d]}"
  harden_zone "$zid"
  if zone_serves_content "$zid" "$d"; then
    warn "$d parece servir contenido real — NO creo dummies ni redirect (revísalo tú)"
  else
    ensure_record "$zid" "$d" A "@" "192.0.2.1" ',"proxied":true'
    ensure_record "$zid" "$d" AAAA "@" "100::" ',"proxied":true'
    ensure_record "$zid" "$d" CNAME "www.$d" "$d" ',"proxied":true'
    set_redirect_ruleset "$zid" "$d" "$(redirect_rules_to "$CANONICAL")" "$d/* -> https://$CANONICAL/*"
  fi
  parked_email_hygiene "$zid" "$d"
done

if [ -n "${ZID[$BILLING]:-}" ]; then
  echo; echo "== $BILLING (reservado SaaS/billing: blindaje sí, contenido no) =="
  zid="${ZID[$BILLING]}"
  harden_zone "$zid"
  if has_mx "$zid"; then
    info "$BILLING tiene MX (correo en uso)"
    has_spf "$zid"            || warn "$BILLING sin SPF — configúralo con tu proveedor"
    has_dmarc "$zid" "$BILLING" || warn "$BILLING sin DMARC — añade al menos p=none"
  else
    parked_email_hygiene "$zid" "$BILLING"
    info "cuando actives email o el SaaS en $BILLING: elimina el null MX y el SPF -all"
  fi
fi

echo
echo "== Resumen: $N_OK ok · $N_SKIP skip · $N_WARN avisos · $N_FAIL fallos =="
[ ${#INACCESSIBLE[@]} -gt 0 ] && echo "   Zonas saltadas: ${INACCESSIBLE[*]} (necesitan token de su cuenta)"
echo
echo "Pasos manuales que la API no cubre:"
echo "  1. 2FA en la(s) cuenta(s) Cloudflare (app o llave física, no SMS)"
echo "  2. Transfer lock + auto-renew: panel Domain Registration de cada dominio"
echo "  3. Revoca este token al terminar"
echo
echo "Verificación (tras unos minutos de propagación):"
echo "  dig +dnssec $CANONICAL SOA"
echo "  curl -sI https://${PARKED[0]}/x | grep -iE 'HTTP|location'"
echo "  dig TXT _dmarc.${PARKED[0]} +short && dig MX ${PARKED[0]} +short"
exit $((N_FAIL > 0 ? 1 : 0))
