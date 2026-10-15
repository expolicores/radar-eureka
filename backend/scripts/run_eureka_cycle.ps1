param([switch]$DryRun, [ValidateSet('manual','scheduled')][string]$Trigger = 'manual')
$ErrorActionPreference = 'Stop'
$CycleBackendRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$CyclePython = Join-Path $CycleBackendRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $CyclePython -PathType Leaf)) { throw 'Python del entorno no encontrado.' }
Push-Location -LiteralPath $CycleBackendRoot
try {
    $CycleArguments = @('-m','public_procurement.entrypoints.cli','run-eureka-cycle','--trigger',$Trigger,'--json')
    if ($DryRun) { $CycleArguments += '--dry-run' }
    & $CyclePython @CycleArguments
    $CycleExit = $LASTEXITCODE
} finally { Pop-Location }
exit $CycleExit
