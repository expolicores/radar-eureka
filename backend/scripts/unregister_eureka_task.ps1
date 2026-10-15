[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param()
$ErrorActionPreference = 'Stop'
$TaskBackendRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$TaskPython = Join-Path $TaskBackendRoot '.venv\Scripts\python.exe'
Push-Location -LiteralPath $TaskBackendRoot
try {
    $TaskRaw = & $TaskPython (Join-Path $PSScriptRoot 'eureka_task_config.py')
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo leer configuración.' }
    $TaskName = ($TaskRaw | ConvertFrom-Json).name
} finally { Pop-Location }
if ($PSCmdlet.ShouldProcess($TaskName, 'Desregistrar únicamente tarea Eureka; conservar datos/logs')) {
    Unregister-ScheduledTask -TaskName $TaskName -TaskPath '\' -Confirm:$false
}
