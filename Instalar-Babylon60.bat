@echo off
REM ==============================================================================
REM BABYLON-60: Instalador Proactivo 1-Clic para Windows (Self-Healing)
REM Especificación: babylon60-architecture v4.3 / C5-REAL
REM ==============================================================================

echo ============================================================
echo       BABYLON IDE -- Secuencia de Ignicion 1-Clic
echo       Hypervisor: MOSKV-1 ^| Ring-0 C-ABI Runtime
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"

REM Comprobacion de UI local
if exist "%SCRIPT_DIR%ui\index.html" (
    echo [1/2] Interfaz Soberana (Ibex Edition) verificada.
    echo [2/2] Desplegando en navegador predeterminado...
    start "" "%SCRIPT_DIR%ui\index.html"
    echo.
    echo [OK] BABYLON IDE arrancado en Modo Standalone.
) else (
    echo [ERROR] No se encuentra ui\index.html.
    pause
    exit /b 1
)
