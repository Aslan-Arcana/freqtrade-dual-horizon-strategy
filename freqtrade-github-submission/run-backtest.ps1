$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$PythonCandidates = @((Join-Path $PSScriptRoot '.venv\Scripts\python.exe'), (Join-Path (Split-Path $PSScriptRoot -Parent) '.venv\Scripts\python.exe'), 'python')
$SelectedPython = $null
foreach ($Candidate in $PythonCandidates) {
    if (Get-Command $Candidate -ErrorAction SilentlyContinue) {
        & $Candidate -c "import freqtrade" 2>$null
        if ($LASTEXITCODE -eq 0) { $SelectedPython=$Candidate; break }
    }
}
$Arguments = @('backtesting','--config','config.shared.json','--userdir','user_data','--strategy','DualHorizonTrendV2','--timerange','20240101-20260101','--fee','0.001','--cache','none','--backtest-directory','user_data/backtest_results/shared-v2','--no-color')
New-Item -ItemType Directory -Force 'user_data/backtest_results/shared-v2' | Out-Null
$ErrorActionPreference = 'Continue'
if ($SelectedPython) {
    & $SelectedPython -m freqtrade @Arguments > backtest.log 2>&1
} elseif (Get-Command freqtrade -ErrorAction SilentlyContinue) {
    & freqtrade @Arguments > backtest.log 2>&1
} else {
    Write-Host 'Freqtrade not found. Activate your Freqtrade Python environment and retry.'
    exit 1
}
$ResultCode = $LASTEXITCODE
Get-Content backtest.log -Tail 100
if ($ResultCode -ne 0) { Write-Host 'FAILED: See backtest.log'; exit $ResultCode }
Write-Host 'Completed. Results: user_data/backtest_results/shared-v2/'
