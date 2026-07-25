$TaskName = "KnowledgeAudit-DailyPipeline"
$ScriptPath = "C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07\daily\run-daily.ps1"
$BaseDir = "C:\Users\Admin\Documents\Codex\knowledge-audit-2026-07"

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
$trigger2 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -WorkingDirectory $BaseDir

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 30) -ExecutionTimeLimit (New-TimeSpan -Hours 2)

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger,$trigger2 -Settings $settings -Principal $principal -Description "Daily knowledge audit 9AM"

Write-Host "Task registered: daily at 9:00 AM"
