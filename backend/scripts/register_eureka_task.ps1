[CmdletBinding(SupportsShouldProcess = $true)]
param()
$ErrorActionPreference = 'Stop'
$TaskBackendRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$TaskPython = Join-Path $TaskBackendRoot '.venv\Scripts\python.exe'
$TaskLauncher = Join-Path $PSScriptRoot 'run_eureka_cycle.ps1'
if (-not (Test-Path -LiteralPath $TaskPython -PathType Leaf)) { throw 'Python del entorno no encontrado.' }
if (-not (Test-Path -LiteralPath $TaskLauncher -PathType Leaf)) { throw 'Launcher no encontrado.' }
Push-Location -LiteralPath $TaskBackendRoot
try {
    $TaskConfigRaw = & $TaskPython (Join-Path $PSScriptRoot 'eureka_task_config.py')
    if ($LASTEXITCODE -ne 0) { throw 'Configuración inválida.' }
    $TaskConfig = $TaskConfigRaw | ConvertFrom-Json
    $TaskPreflightRaw = & $TaskPython -m public_procurement.entrypoints.cli run-eureka-cycle --dry-run --json
    if ($LASTEXITCODE -ne 0) { throw 'Preflight falló.' }
    $TaskPreflight = $TaskPreflightRaw | ConvertFrom-Json
    if (-not $TaskPreflight.schema_ready) { throw 'Falta migración 0016 autorizada.' }
} finally { Pop-Location }
if ($TaskConfig.timezone -ne 'America/Bogota' -or (Get-TimeZone).Id -ne 'SA Pacific Standard Time') {
    throw 'El scheduler inicial requiere Windows en SA Pacific Standard Time y configuración America/Bogota.'
}
if (-not $TaskConfig.enabled -and -not $WhatIfPreference) { throw 'Habilita explícitamente automation antes de registrar.' }
$TaskTriggers = @()
if ($TaskConfig.times) {
    foreach ($TaskTime in $TaskConfig.times.Split(',')) {
        $TaskTriggers += New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.Add([timespan]::Parse($TaskTime.Trim())))
    }
} else {
    $TaskTriggers += New-ScheduledTaskTrigger -Once -At ([datetimeoffset]::Parse($TaskPreflight.next_theoretical).LocalDateTime) -RepetitionInterval (New-TimeSpan -Hours $TaskConfig.interval)
}
$TaskSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([timespan]::Zero)
$TaskSettings.WakeToRun = $false
$TaskAction = New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $TaskLauncher + '" -Trigger scheduled') -WorkingDirectory $TaskBackendRoot
$TaskPrincipal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
if ($PSCmdlet.ShouldProcess($TaskConfig.name, 'Registrar tarea Eureka; reemplazar si ya existe')) {
    Register-ScheduledTask -TaskName $TaskConfig.name -TaskPath '\' -Action $TaskAction -Trigger $TaskTriggers -Settings $TaskSettings -Principal $TaskPrincipal -Force | Out-Null
    Get-ScheduledTaskInfo -TaskName $TaskConfig.name -TaskPath '\' | Select-Object TaskName, NextRunTime, LastTaskResult
}
