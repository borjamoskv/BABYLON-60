# 🧹 Plan de Limpieza del Historial Git — P0

> ⏰ Ejecutar INMEDIATAMENTE cuando se detecte un secreto en el historial.
> ⚡ PRIMERO rotar el secreto, DESPUÉS limpiar el historial.

---

## Paso 0 — Contención Inmediata (< 15 min)

```bash
# 1. ROTAR el secreto expuesto AHORA (antes de limpiar)
#    → Ir al proveedor (AWS/GCP/Stripe/etc) y regenerar
#    → Actualizar en secrets manager / vault
#    → Desplegar la rotación

# 2. Si el repo es público → hacerlo PRIVADO temporalmente
gh repo edit OWNER/REPO --visibility private

# 3. Revocar tokens de GitHub si se expusieron
gh auth logout
```

## Paso 1 — Identificar qué limpiar

```bash
# Escanear TODO el historial
gitleaks detect --source . --verbose --report-format json --report-path leaks.json

# Ver qué se encontró
cat leaks.json | jq '.[].File' | sort -u

# Buscar un secreto específico en historial
git log -p --all -S 'TU_SECRETO_AQUI' --diff-filter=ACDMR
git log -p --all -S 'AKIA'  # Ejemplo: AWS keys

# Listar archivos sensibles que alguna vez existieron
git log --all --full-history -- '*.pem' '*.key' '.env' 'credentials.json'
```

## Paso 2 — Limpiar con git-filter-repo (RECOMENDADO)

```bash
# Instalar
pip install git-filter-repo

# BACKUP del repo
cp -r .git .git-backup

# Opción A: Eliminar archivos específicos del historial completo
git filter-repo --invert-paths --path .env
git filter-repo --invert-paths --path config/secrets.yml
git filter-repo --invert-paths --path certs/private.key

# Opción B: Eliminar múltiples archivos de una vez
cat <<EOF > paths-to-remove.txt
.env
.env.production
config/database.yml
secrets/
credentials.json
*.pem
*.key
EOF
git filter-repo --invert-paths --paths-from-file paths-to-remove.txt

# Opción C: Reemplazar texto (secreto → REDACTED)
cat <<EOF > replacements.txt
AKIAIOSFODNN7EXAMPLE==>REDACTED_AWS_KEY
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY==>REDACTED_AWS_SECRET
EOF
git filter-repo --replace-text replacements.txt
```

## Paso 3 — Force Push (coordinado con el equipo)

```bash
# ⚠️  AVISAR AL EQUIPO antes de ejecutar esto

# Verificar que la limpieza funcionó
gitleaks detect --source . --verbose
# Debe dar: no leaks found ✅

# Push forzado
git push origin --force --all
git push origin --force --tags

# Limpiar reflog local
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

## Paso 4 — Post-limpieza (todos los developers)

```bash
# CADA developer del equipo debe ejecutar:
cd /path/to/repo
git fetch origin
git reset --hard origin/main    # ⚠️ Pierde cambios locales no pusheados

# O mejor: clonar de nuevo
cd ..
rm -rf repo-viejo
git clone <URL_DEL_REPO>
```

## Paso 5 — Verificación y Cierre

```bash
# 1. Escaneo completo post-limpieza
gitleaks detect --source . --verbose
# ✅ Debe reportar 0 leaks

# 2. Verificar que el secreto rotado funciona en producción
curl -H "Authorization: Bearer $NEW_TOKEN" https://api.example.com/health

# 3. Verificar que el secreto viejo NO funciona
curl -H "Authorization: Bearer $OLD_TOKEN" https://api.example.com/health
# ✅ Debe dar 401/403
```

## Paso 6 — Documentar el Incidente

| Campo                    | Valor                    |
| ------------------------ | ------------------------ |
| Fecha de detección       | YYYY-MM-DD HH:MM        |
| Secreto expuesto         | Tipo (AWS key, DB pass…) |
| Commits afectados        | abc1234..def5678         |
| ¿Repo era público?      | Sí / No                 |
| Tiempo de exposición     | X días/horas             |
| Secreto rotado           | ✅ Sí — Fecha            |
| Historial limpiado       | ✅ Sí — Fecha            |
| Verificado por           | @nombre                  |
| Acceso no autorizado     | Sí / No / Desconocido   |

---

> 🔁 **Después de cada incidente**: Revisar por qué el pre-commit
> hook no lo atrapó y actualizar las reglas.
