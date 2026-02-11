$Action = New-ScheduledTaskAction -Execute "python" -Argument "c:\prospect\prospect\run_system.py"
$Trigger = New-ScheduledTaskTrigger -Daily -At 9am
$Principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -TaskName "DailyProspectingRun" -Description "Runs the automated prospecting system daily at 9 AM."

Write-Host "Task 'DailyProspectingRun' created successfully. It will run daily at 9 AM."
Write-Host "To run it manually for testing: Start-ScheduledTask -TaskName 'DailyProspectingRun'"
