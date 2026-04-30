# launch_nexus.ps1
# Run Core Nexus with optional admin elevation
# Usage: .\launch_nexus.ps1 [-TextMode] [-AsAdmin]

param(
    [switch]$TextMode,
    [switch]$AsAdmin
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$NexusScript = Join-Path $ScriptDir "core_nexus.py"

# Verify ANTHROPIC_API_KEY
if (-not $env:ANTHROPIC_API_KEY) {
    Write-Host "[ERROR] ANTHROPIC_API_KEY is not set." -ForegroundColor Red
    Write-Host "Set it with:"
    Write-Host '  $env:ANTHROPIC_API_KEY = "sk-ant-..."' -ForegroundColor Yellow
    Write-Host "Or permanently:"
    Write-Host '  [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY","sk-ant-...","User")' -ForegroundColor Yellow
    exit 1
}

$args_list = @($NexusScript)
if ($TextMode) { $args_list += "--text" }

if ($AsAdmin) {
    # Re-launch as admin, passing the API key
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = $args_list -join " "
    $psi.Verb = "runas"
    $psi.UseShellExecute = $true
    $psi.EnvironmentVariables["ANTHROPIC_API_KEY"] = $env:ANTHROPIC_API_KEY
    [System.Diagnostics.Process]::Start($psi) | Out-Null
} else {
    Write-Host ""
    Write-Host " Starting Core Nexus..." -ForegroundColor Cyan
    python @args_list
}
