# Imperial Restaurant OS - Script de Inicio (PowerShell)
$ErrorActionPreference = "Continue"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "      IMPERIAL RESTAURANT OS - INICIADOR DE SERVIDORES" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Docker DB / Redis (opcional si Docker está abierto)
Write-Host "[1/3] Verificando Docker para PostgreSQL y Redis..." -ForegroundColor Yellow
try {
    $dockerCheck = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " - Levantando db y redis en segundo plano..." -ForegroundColor Gray
        docker compose up -d db redis | Out-Null
        Write-Host " - Contenedores auxiliares listos." -ForegroundColor Green
    } else {
        Write-Host " - Docker no está en ejecución. Saltando paso Docker..." -ForegroundColor DarkYellow
    }
} catch {
    Write-Host " - Docker no disponible. Saltando paso Docker..." -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "[2/3] Levantando Backend (FastAPI / Uvicorn)..." -ForegroundColor Yellow
$BackendCmd = "cd '$RootPath\backend'; if (Test-Path '../venv/Scripts/Activate.ps1') { & '../venv/Scripts/Activate.ps1' }; uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCmd

Write-Host "[3/3] Levantando Frontend (Vite React)..." -ForegroundColor Yellow
$FrontendCmd = "cd '$RootPath\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCmd

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host " Servidores lanzados en ventanas independientes:" -ForegroundColor Green
Write-Host "  - Backend API: http://127.0.0.1:8000 (Swagger: /docs)" -ForegroundColor White
Write-Host "  - Frontend:    http://127.0.0.1:5173" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
