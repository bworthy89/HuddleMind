$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$script = Join-Path $repoPath 'bridge\send_hosted_background.ps1'
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
# Interactive logon preserves access to this user's DPAPI credential without a password.
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -File `"$script`"" -WorkingDirectory $repoPath
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 4)
Register-ScheduledTask -TaskName 'HuddleMind Hosted Delivery' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Retry pending HuddleMind observations every five minutes while logged in.' -Force | Out-Null
Start-ScheduledTask -TaskName 'HuddleMind Hosted Delivery'
Write-Output 'HuddleMind delivery task registered and started.'
