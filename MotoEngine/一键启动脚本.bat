@echo off
setlocal
chcp 65001 >nul
title MotoEngine One-Click Start

set "ROOT=%~dp0"
set "VENV_PY=%ROOT%.venv\Scripts\python.exe"
set "PORT=8000"

echo ==============================
echo  MotoEngine One-Click Start
echo ==============================

if not exist "%VENV_PY%" (
    echo Virtual environment not found:
    echo %VENV_PY%
    echo Please create or restore .venv under the MotoEngine folder first.
    pause
    exit /b 1
)

pushd "%ROOT%"

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING"') do set "OLD_PID=%%P"
if defined OLD_PID (
    echo Port %PORT% is already in use by PID %OLD_PID%.
    echo Stopping the old process first...
    taskkill /PID %OLD_PID% /F >nul 2>nul
    timeout /t 2 /nobreak >nul
)

echo Starting backend...
start "MotoEngine Backend" cmd /k ""%VENV_PY%" -m motoengine"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo Opening home page...
start "" "http://127.0.0.1:%PORT%/"

echo Opening agent page...
start "" "http://127.0.0.1:%PORT%/agent/"

echo ==============================
echo  Started successfully
echo  Home:   http://127.0.0.1:%PORT%/
echo  Agent:  http://127.0.0.1:%PORT%/agent/
echo  API:    http://127.0.0.1:%PORT%/api-docs
echo ==============================
popd
pause
