# PowerShell script to activate a virtual environment (if present) and run two Python scripts.
# Save as: /c:/Users/User/Desktop/Projects/fyp/backend/investingService/newsProcessing.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvNames = @('venv', '.venv', 'env')

$activated = $false
foreach ($name in $venvNames) {
    $activatePath = Join-Path $scriptDir "$name\Scripts\Activate.ps1"
    if (Test-Path $activatePath) {
        Write-Host "Activating virtual environment: $name"
        . $activatePath
        $activated = $true
        break
    }
}

if (-not $activated) {
    Write-Host "No virtual environment activation script found. Will use 'python' from PATH."
}

function Run-PythonStockPredictionScript {
    param([string]$scriptName)
    $scriptPath = Join-Path $scriptDir $scriptName
    if (-not (Test-Path $scriptPath)) {
        Write-Error "Script not found: $scriptPath"
        exit 2
    }

    Write-Host "Running: python $scriptPath"
    & python $scriptPath --all --save
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Error "Script $scriptName exited with code $code"
        exit $code
    }
}

PythonStockPredictionScript -scriptName 'scrapeNews.py'

Write-Host "All scripts completed successfully."
exit 0