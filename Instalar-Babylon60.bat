@echo off
setlocal
REM ==============================================================================
REM BABYLON-60: Instalador Proactivo 1-Clic para Windows (Self-Healing)
REM Especificacion: babylon60-architecture v4.3 / C5-REAL
REM ==============================================================================

echo ============================================================
echo       BABYLON IDE -- Secuencia de Ignicion 1-Clic
echo       Hypervisor: MOSKV-1 ^| Ring-0 C-ABI Runtime
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [1/4] Verificando dependencias del sistema (Rust y uv)...
where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Error: 'cargo' ^(Rust^) no detectado en el PATH.
    echo [+] Instala Rust desde: https://rustup.rs/
    pause
    exit /b 1
)

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Error: 'uv' ^(Python package manager^) no detectado en el PATH.
    echo [+] Instala uv desde: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo [2/4] Aprovisionando Ring-0 (Silicio / Rust)...
cargo build --workspace
if %errorlevel% neq 0 (
    echo [!] Error en la compilacion del Ring-0. Abortando.
    pause
    exit /b 1
)

echo [3/4] Aprovisionando Ring-1 (Exocortex / Python)...
uv sync
if %errorlevel% neq 0 (
    echo [!] Error en la sincronizacion de dependencias Python. Abortando.
    pause
    exit /b 1
)

echo [4/4] Transfiriendo control a MOSKV-1...
echo ============================================================
echo.

cargo run --bin babylon60_kernel -- unbox
if %errorlevel% neq 0 (
    uv run python scripts\c5_setup\unboxing_moskv1.py
)

pause
