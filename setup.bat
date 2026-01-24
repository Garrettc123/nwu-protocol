@echo off
REM NWU Protocol - One-Command Setup Script for Windows
REM Usage: setup.bat

setlocal enabledelayedexpansion

color 0A
echo.
echo ========================================================
echo    NWU PROTOCOL - Windows Automated Setup
echo ========================================================
echo.

REM Check for Docker
echo [*] Checking prerequisites...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [X] Docker not found!
    echo.
    echo Please install Docker Desktop from:
    echo https://docs.docker.com/desktop/install/windows-install/
    echo.
    pause
    exit /b 1
)

echo [+] Docker is installed

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [X] Docker Compose not found!
    echo.
    echo Please install Docker Desktop (includes Compose):
    echo https://docs.docker.com/desktop/install/windows-install/
    echo.
    pause
    exit /b 1
)

echo [+] Docker Compose is installed
echo.

REM Setup environment file
if not exist .env (
    echo [*] Creating .env file...
    copy .env.example .env >nul
    
    echo.
    set /p "OPENAI_KEY=Enter your OpenAI API Key (or press Enter to skip): "
    
    if not "!OPENAI_KEY!"=="" (
        powershell -Command "(Get-Content .env) -replace 'your-openai-api-key-here', '!OPENAI_KEY!' | Set-Content .env"
        echo [+] API key configured
    ) else (
        echo [!] You can add your API key later in .env file
    )
) else (
    echo [+] .env file already exists
)

echo.
echo [*] Pulling Docker images...
docker-compose pull

echo.
echo [*] Starting all services...
docker-compose up -d

echo.
echo [*] Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

echo.
echo [*] Checking service health...
docker-compose ps

echo.
echo ========================================================
echo    SETUP COMPLETE!
echo ========================================================
echo.
echo [+] Access Your Services:
echo.
echo    Frontend:     http://localhost:3000
echo    Backend API:  http://localhost:8000
echo    API Docs:     http://localhost:8000/docs
echo    RabbitMQ:     http://localhost:15672 (guest/guest)
echo.
echo ========================================================
echo.
echo [i] Quick Commands:
echo    status.bat    - Check all service status
echo    logs.bat      - View service logs
echo    stop.bat      - Stop all services
echo    restart.bat   - Restart all services
echo.
echo ========================================================
echo.
echo Need help? Run: help.bat
echo.
pause
