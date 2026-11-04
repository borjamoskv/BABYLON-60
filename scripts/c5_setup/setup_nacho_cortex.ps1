# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ CORTEX FULL ENVIRONMENT SETUP (WINDOWS POWERSHELL)
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "[CORTEX-SETUP-WIN] Instalando entorno agéntico completo CORTEX en Windows..." -ForegroundColor Cyan

# 1. Rutas de configuración
$UserProfile = $env:USERPROFILE
$CortexSkillsDir = Join-Path $UserProfile ".gemini\config\skills"
$CortexConfigDir = Join-Path $UserProfile ".gemini\config"

if (-not (Test-Path $CortexSkillsDir)) {
    New-Item -ItemType Directory -Path $CortexSkillsDir -Force | Out-Null
}

Write-Host "[1/4] Directorios configurados en: $CortexSkillsDir" -ForegroundColor Green

# 2. Copiar reglas de workspace
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Split-Path -Parent $ScriptDir
$WorkspaceAgents = Join-Path $RepoRoot ".agents"
$DestAgents = Join-Path $UserProfile ".agents"

if (Test-Path $WorkspaceAgents) {
    Write-Host "[2/4] Copiando gobernanza de workspace a $DestAgents..." -ForegroundColor Green
    Copy-Item -Path $WorkspaceAgents -Destination $DestAgents -Recurse -Force -ErrorAction SilentlyContinue
}

# 3. Comprobar binarios del sistema en Windows
Write-Host "[3/4] Comprobando binarios en Windows..." -ForegroundColor Green

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "  ✔ git.exe detectado" -ForegroundColor DarkGreen
} else {
    Write-Host "  ⚠️ Git no instalado en PATH (Ejecutar: winget install Git.Git)" -ForegroundColor Yellow
}

if (Get-Command jj -ErrorAction SilentlyContinue) {
    Write-Host "  ✔ jj.exe detectado" -ForegroundColor DarkGreen
} else {
    Write-Host "  ⚠️ Jujutsu (jj) no instalado (Ejecutar: cargo install jj-cli o winget install jj)" -ForegroundColor Yellow
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "  ✔ python.exe detectado" -ForegroundColor DarkGreen
} else {
    Write-Host "  ⚠️ Python no instalado en PATH" -ForegroundColor Yellow
}

# 4. Verificación de variables de entorno
Write-Host "[4/4] Verificando variables de entorno..." -ForegroundColor Green
if (-not $env:KIMI_API_KEY) {
    Write-Host "  ⚠️ Recuerda configurar KIMI_API_KEY en PowerShell:" -ForegroundColor Yellow
    Write-Host '     $env:KIMI_API_KEY="tu_clave_moonshot"' -ForegroundColor Gray
}

Write-Host "`n✅ [CORTEX-SETUP-WIN] ¡Entorno Windows preparado con éxito!" -ForegroundColor Cyan
