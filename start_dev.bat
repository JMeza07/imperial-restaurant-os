@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

title Imperial Restaurant OS - Starter

echo ========================================================
echo        IMPERIAL RESTAURANT OS - INICIADOR DE SERVIDORES
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando contenedores auxiliares (PostgreSQL, Redis)...
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    docker compose up -d db redis >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo  - Base de datos y Redis iniciados con Docker.
    ) else (
        echo  - Docker disponible pero falló al levantar db/redis (continuando en modo local)...
    )
) else (
    echo  - Docker no está activo o no está instalado. Continuando con servicios locales...
)

echo.
echo [2/3] Levantando Backend (FastAPI en http://127.0.0.1:8000)...
start "Backend - Imperial OS" cmd /k "cd /d "%~dp0backend" && if exist ..\venv\Scripts\activate.bat (call ..\venv\Scripts\activate.bat) else (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && uvicorn app.main:app --reload --port 8000"

echo [3/3] Levantando Frontend (Vite en http://127.0.0.1:5173)...
start "Frontend - Imperial OS" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================================
echo  Servidores iniciados en ventanas independientes:
echo   - Backend:  http://127.0.0.1:8000 (Docs: /docs)
echo   - Frontend: http://127.0.0.1:5173
echo ========================================================
echo.
pause
