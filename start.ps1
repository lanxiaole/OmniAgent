param(
    [string]$Mode = "both"
)

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path $MyInvocation.MyCommand.Path -Parent
$VENV_PATH = Join-Path $PROJECT_ROOT ".venv"
$PYTHON = Join-Path $VENV_PATH "Scripts\python.exe"
$UVICORN = Join-Path $VENV_PATH "Scripts\uvicorn.exe"
$NPM = "npm"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "          OmniAgent Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not (Test-Path $VENV_PATH)) {
    Write-Host "Error: Virtual environment not found at $VENV_PATH" -ForegroundColor Red
    Write-Host "Please run: uv sync" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[1/5] Cleaning up existing services..." -ForegroundColor Green
$ports = @(8000, 5173)
foreach ($port in $ports) {
    $connections = netstat -ano | Select-String -Pattern ":$port\s+.*LISTENING" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Where-Object { $_ -match '^\d+$' } | Select-Object -Unique

    foreach ($pid in $connections) {
        Write-Host "      Port $port is occupied by PID $pid, terminating..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "      ✅ Process $pid terminated" -ForegroundColor Green
        } catch {
            Write-Host "      ⚠️  Failed to terminate process $pid (may need admin privileges)" -ForegroundColor Yellow
        }
    }
}
Start-Sleep -Seconds 1
Write-Host "      ✅ Port cleanup completed" -ForegroundColor Green

Write-Host "`n[2/5] Activating virtual environment..." -ForegroundColor Green
& $PYTHON -c "import sys; print(f'Python: {sys.version}')"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

if ($Mode -eq "both" -or $Mode -eq "backend") {
    Write-Host "`n[3/5] Starting backend service..." -ForegroundColor Green
    Write-Host "      Backend: http://localhost:8000" -ForegroundColor Gray
    
    $backendJob = Start-Job -ScriptBlock {
        param($uvicorn, $projectRoot)
        Set-Location $projectRoot
        & $uvicorn "backend.main:app" --reload --port 8000
    } -ArgumentList $UVICORN, $PROJECT_ROOT

    Start-Sleep -Seconds 3

    $response = $null
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 5
    } catch {
        Write-Host "Warning: Backend may need more time to start" -ForegroundColor Yellow
    }
    
    if ($response -and $response.StatusCode -eq 200) {
        Write-Host "      ✅ Backend started successfully" -ForegroundColor Green
    } else {
        Write-Host "      ⚠️  Backend starting..." -ForegroundColor Yellow
    }
}

if ($Mode -eq "both" -or $Mode -eq "frontend") {
    Write-Host "`n[4/5] Starting frontend dev server..." -ForegroundColor Green
    Write-Host "      Frontend: http://localhost:5173" -ForegroundColor Gray
    
    $frontendJob = Start-Job -ScriptBlock {
        param($npm, $projectRoot)
        Set-Location (Join-Path $projectRoot "frontend")
        & $npm run dev
    } -ArgumentList $NPM, $PROJECT_ROOT

    Start-Sleep -Seconds 3
    Write-Host "      ⚠️  Frontend starting..." -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "          Services Started" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

while ($true) {
    Start-Sleep -Seconds 1
}