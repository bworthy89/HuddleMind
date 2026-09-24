param([string]$DynastyId = '08eb1fdc-de1b-405a-adc0-4dc684459747')
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$credentialPath = Join-Path $repoPath 'local_data\hosted-token.xml'
if (-not (Test-Path -LiteralPath $credentialPath)) {
    throw 'Hosted credential has not been configured for this Windows user.'
}
# Windows DPAPI protects the saved credential for this Windows user and PC.
$credential = Import-Clixml -LiteralPath $credentialPath
$previousToken = $env:HUDDLEMIND_RECEIVER_TOKEN
Push-Location $repoPath
try {
    $env:HUDDLEMIND_RECEIVER_TOKEN = $credential.GetNetworkCredential().Password
    & (Join-Path $repoPath '.venv\Scripts\python.exe') -m bridge.send_observations $DynastyId --receiver 'https://huddlemind-api.worthymedia.tech' --database (Join-Path $repoPath 'local_data\huddlemind.sqlite3')
    if ($LASTEXITCODE -ne 0) { throw "Sender failed with exit code $LASTEXITCODE" }
}
finally {
    $env:HUDDLEMIND_RECEIVER_TOKEN = $previousToken
    Pop-Location
}
