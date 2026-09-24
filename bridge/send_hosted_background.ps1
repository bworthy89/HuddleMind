# Task Scheduler runs this wrapper as the same user who encrypted the credential.
$ErrorActionPreference = 'Stop'
$statusPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'local_data\hosted-delivery-status.json'
$status = @{ attempted_at = [DateTime]::UtcNow.ToString('o'); success = $false }
try {
    $output = & (Join-Path $PSScriptRoot 'send_hosted.ps1') 2>&1
    $status.success = $true
    $status.message = ($output | Out-String).Trim()
}
catch {
    # Keep only the latest result; never log credentials or observation payloads.
    $status.message = $_.Exception.Message
}
$temporary = "$statusPath.tmp"
$status | ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding UTF8
Move-Item -LiteralPath $temporary -Destination $statusPath -Force
if (-not $status.success) { exit 1 }
