param(
    [string]$Save = "$env:USERPROFILE\OneDrive\Documents\EA SPORTS College Football 27\saves\DYNASTY-TULANENEW-AUTOSAVE",
    [string]$Schema = 'E:\aibridgemod\schema-discovery\CFB27_833_0.gz',
    [string]$DynastyId = '08eb1fdc-de1b-405a-adc0-4dc684459747'
)
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
# Capture runs in this terminal; the existing scheduled sender handles networking.
Push-Location $repoPath
try {
    & (Join-Path $repoPath '.venv\Scripts\python.exe') -u -m bridge.watch_capture $Save $Schema $DynastyId --database (Join-Path $repoPath 'local_data\huddlemind.sqlite3')
    if ($LASTEXITCODE -ne 0) { throw "Capture watcher failed with exit code $LASTEXITCODE" }
}
finally { Pop-Location }
