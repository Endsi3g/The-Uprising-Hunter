$WorkDir = "c:\prospect\prospect"
$PythonPath = "$WorkDir\venv\Scripts\python.exe"
$ScriptPath = "$WorkDir\run_system.py"

# Use venv python if exists, else system python
if (-Not (Test-Path $PythonPath)) {
    Write-Host "Virtual environment not found, using system python."
    $PythonPath = "python"
}

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath -WorkingDirectory $WorkDir
$Trigger = New-ScheduledTaskTrigger -Daily -At 9am
$Principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

$TaskName = "DailyProspectingRun"

# Unregister if exists to update
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -TaskName $TaskName -Description "Runs the automated prospecting system daily at 9 AM."

Write-Host "Task '$TaskName' created/updated successfully."
Write-Host " It will run daily at 9 AM using: $PythonPath"
Write-Host "To run it manually: Start-ScheduledTask -TaskName '$TaskName'"
