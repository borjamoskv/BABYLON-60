# Install the terminal CLI and stdio memory MCP server on Windows.
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Mcp,
    [string]$Ledger,
    [ValidateSet("codex")]
    [string]$Client
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ($Mcp -and $Client) {
    throw "-Client cannot be combined with -Mcp; activate Codex separately before starting the stdio server."
}
if ($Client) { $Client = $Client.ToLowerInvariant() }
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
$repoRoot = $PSScriptRoot
$required = @(
    "pyproject.toml", "uv.lock",
    "01_KISH_ENGINE/babylon60/cli/main_dispatcher.py",
    "01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py",
    "01_KISH_ENGINE/babylon60/presentation.md"
)
foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $relative) -PathType Leaf)) {
        throw "Missing distribution file: $relative"
    }
}
$cli = Join-Path $repoRoot ".venv/Scripts/babylon60.exe"
$server = Join-Path $repoRoot ".venv/Scripts/babylon60-mcp.exe"
if ($DryRun) {
    Write-Output "BABYLON_TERMINAL_VERIFIED: $repoRoot"
    Write-Output "Install: uv sync --locked --no-dev --no-editable"
    Write-Output "CLI: $cli"
    Write-Output "MCP stdio: $server"
    $quotedCli = "'" + $cli.Replace("'", "''") + "'"
    if ($Client) {
        Write-Output "Setup preview after installation (not executed): & $quotedCli setup --client codex --dry-run"
        Write-Output "Installation and activation are planned only; no executables or global settings are changed."
    } elseif ($Mcp) {
        $quotedServer = "'" + $server.Replace("'", "''") + "'"
        $ledgerArgument = if ($Ledger) { " --ledger '" + $Ledger.Replace("'", "''") + "'" } else { "" }
        Write-Output "Start after installation: & $quotedServer$ledgerArgument"
    } else {
        Write-Output "Codex integration: not activated."
        Write-Output "Activate after installation: & $quotedCli setup --client codex"
    }
    return
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/"
}
if (Test-Path -LiteralPath (Join-Path $repoRoot ".git")) {
    $changes = & git -C $repoRoot status --porcelain
    if ($LASTEXITCODE -ne 0) { throw "Cannot verify checkout state" }
    if ($changes) {
        throw "Install from a clean checkout/worktree or the source release bundle; local changes are preserved."
    }
}
Push-Location -LiteralPath $repoRoot
try {
    # A wheel installation avoids locale-dependent .pth decoding on Python 3.11.
    # Keep installation logs away from the stdio MCP protocol's stdout.
    & uv sync --locked --no-dev --no-editable | ForEach-Object { [Console]::Error.WriteLine($_) }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    if (-not (Test-Path -LiteralPath $cli -PathType Leaf) -or
        -not (Test-Path -LiteralPath $server -PathType Leaf)) {
        throw "Installation did not create the CLI and MCP executables"
    }
    if ($Mcp) {
        if ($Ledger) { & $server --ledger $Ledger } else { & $server }
        exit $LASTEXITCODE
    }
    if ($Client) {
        & $cli setup --client $Client
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } else {
        & $cli --help
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    Write-Output "CLI installed: $cli"
    Write-Output "MCP stdio: $server"
    if ($Client) {
        Write-Output "Next step: open a new Codex conversation to load Babylon; application of the preferences is not yet evaluated."
    } else {
        $quotedCli = "'" + $cli.Replace("'", "''") + "'"
        Write-Output "Codex integration: not activated."
        Write-Output "Next step: & $quotedCli setup --client codex"
    }
}
finally {
    Pop-Location
}
