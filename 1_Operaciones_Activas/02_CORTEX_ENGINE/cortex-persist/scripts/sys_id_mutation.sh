#!/usr/bin/env bash
# [C5-REAL] Exergy-Maximized — SYS_ID Mutation Script
#
# PROPÓSITO: Renombrar la cuenta y carpeta principal de 'borjafernandezangulo' a 'borjamoskv'
# REQUISITOS:
#   1. Debe ejecutarse desde una cuenta de administrador secundaria (NO desde borjafernandezangulo).
#   2. Debe ejecutarse con privilegios sudo.

set -e

OLD_USER="borjafernandezangulo"
NEW_USER="borjamoskv"

OLD_HOME="/Users/$OLD_USER"
NEW_HOME="/Users/$NEW_USER"

# 1. Validación de Entorno
CURRENT_USER=$(stat -f "%Su" /dev/console)
if [ "$CURRENT_USER" = "$OLD_USER" ]; then
    echo "[!] ALERTA DE CRASH CAUSAL (C5-REAL)"
    echo "No puedes mutar la cuenta '$OLD_USER' mientras estás logueado en ella."
    echo "Pasos requeridos:"
    echo "  1. Crea o usa otra cuenta de Administrador."
    echo "  2. Inicia sesión en esa cuenta secundaria."
    echo "  3. Ejecuta este script usando 'sudo'."
    exit 1
fi

if [ "$EUID" -ne 0 ]; then
    echo "[!] Este script requiere privilegios root. Ejecuta: sudo $0"
    exit 1
fi

if ! dscl . -list /Users | grep -q "^$OLD_USER$"; then
    echo "[!] El usuario $OLD_USER no existe en este sistema."
    exit 1
fi

# 2. Mutación Física de la Carpeta Cero
echo "[C5-REAL] Mutando directorio físico..."
if [ -d "$OLD_HOME" ]; then
    mv "$OLD_HOME" "$NEW_HOME"
    echo "  -> Movido: $OLD_HOME a $NEW_HOME"
else
    echo "[!] No se encontró el directorio origen $OLD_HOME."
    exit 1
fi

# 3. Mutación en el Directorio Abierto de macOS (dscl)
echo "[C5-REAL] Mutando OpenDirectory (dscl)..."

# Cambiar la ruta del Home
dscl . -change /Users/$OLD_USER NFSHomeDirectory "$OLD_HOME" "$NEW_HOME"

# Cambiar el Short Name (RecordName)
# OJO: dscl requiere que agreguemos el nuevo nombre y luego eliminemos el viejo
dscl . -append /Users/$OLD_USER RecordName "$NEW_USER"
dscl . -delete /Users/$OLD_USER RecordName "$OLD_USER"

# Forzar actualización de caché
echo "[C5-REAL] Limpiando cachés de directorio..."
dscacheutil -flushcache

echo ""
echo "[✓] MUTACIÓN ESTRUCTURAL COMPLETADA"
echo "La cuenta ha sido migrada a: $NEW_USER"
echo "El nuevo directorio base es: $NEW_HOME"
echo ""
echo "POR FAVOR REINICIA LA MÁQUINA para evitar estados huérfanos antes de iniciar sesión en $NEW_USER."
