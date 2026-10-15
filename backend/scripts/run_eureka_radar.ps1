param(
    [string]$FromDate,
    [string[]]$Department,
    [switch]$DryRun,
    [int]$MaxProcesses = 20,
    [switch]$Json,
    [switch]$ShowSchedule
)

$ErrorActionPreference = "Stop"
$RadarBackendRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$RadarPython = Join-Path $RadarBackendRoot ".venv\Scripts\python.exe"
Push-Location -LiteralPath $RadarBackendRoot
try {
    if ($ShowSchedule) {
        & $RadarPython -c "from public_procurement.shared.config import load_settings; print('Intervalo externo (horas):', load_settings().eureka_radar_interval_hours)"
    } else {
        $RadarArguments = @("-m", "public_procurement.entrypoints.cli", "run-eureka-radar", "--max-processes", [string]$MaxProcesses)
        if ($FromDate) { $RadarArguments += @("--from-date", $FromDate) }
        foreach ($RadarRegion in $Department) { $RadarArguments += @("--department", $RadarRegion) }
        if ($DryRun) { $RadarArguments += "--dry-run" }
        if ($Json) { $RadarArguments += "--json" }
        & $RadarPython @RadarArguments
    }
    $RadarExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $RadarExitCode
