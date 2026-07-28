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

Write-Host "`n[1/3] Cleaning up existing services..." -ForegroundColor Green
$ports = @(8000, 5173)
foreach ($port in $ports) {
    $connections = netstat -ano | Select-String -Pattern ":$port\s+.*LISTENING" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Where-Object { $_ -match '^\d+$' } | Select-Object -Unique

    foreach ($procId in $connections) {
        Write-Host "      Port $port is occupied by PID $procId, terminating..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Host "      ✅ Process $procId terminated" -ForegroundColor Green
        } catch {
            Write-Host "      ⚠️  Failed to terminate process $procId (may need admin privileges)" -ForegroundColor Yellow
        }
    }
}
Start-Sleep -Seconds 1
Write-Host "      ✅ Port cleanup completed" -ForegroundColor Green

Write-Host "`n[2/3] Activating virtual environment..." -ForegroundColor Green
& $PYTHON -c "import sys; print(f'Python: {sys.version}')"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

if ($Mode -eq "both" -or $Mode -eq "backend") {
    Write-Host "`n[3/3] Starting backend service..." -ForegroundColor Green
    Write-Host "      Backend: http://localhost:8000" -ForegroundColor Gray
    
    # 使用 Start-Process 启动后端（独立窗口，更稳定）
    Start-Process -FilePath $UVICORN -ArgumentList "backend.main:app", "--reload", "--port", "8000" -WorkingDirectory $PROJECT_ROOT -WindowStyle Minimized
    
    Start-Sleep -Seconds 3

    # 验证后端是否启动成功
    $maxRetries = 5
    $started = $false
    for ($i = 0; $i -lt $maxRetries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                $started = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    
    if ($started) {
        Write-Host "      ✅ Backend started successfully" -ForegroundColor Green
    } else {
        Write-Host "      ⚠️  Backend starting... (may need more time)" -ForegroundColor Yellow
    }
}

if ($Mode -eq "both" -or $Mode -eq "frontend") {
    Write-Host "`n[3/3] Starting frontend dev server..." -ForegroundColor Green
    Write-Host "      Frontend: http://localhost:5173" -ForegroundColor Gray
    
    # 使用 Start-Process 启动前端（独立窗口）
    $frontendDir = Join-Path $PROJECT_ROOT "frontend"
    Start-Process -FilePath "cmd" -ArgumentList "/c", "cd /d `"$frontendDir`" && npm run dev" -WindowStyle Minimized
    
    Start-Sleep -Seconds 3
    Write-Host "      ✅ Frontend starting..." -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "          Services Started" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "Services are running in separate windows." -ForegroundColor Yellow
Write-Host "Close those windows to stop the services." -ForegroundColor Yellow
Write-Host ""