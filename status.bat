@echo off
REM Service Status Checker for Windows

color 0B
echo.
echo ========================================================
echo    NWU PROTOCOL - Service Status
echo ========================================================
echo.

echo [*] Docker Containers:
echo.
docker-compose ps

echo.
echo [*] Service Health Checks:
echo.

curl -s --max-time 2 http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [X] Frontend is DOWN
) else (
    echo [+] Frontend is UP
)

curl -s --max-time 2 http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [X] Backend API is DOWN
) else (
    echo [+] Backend API is UP
)

curl -s --max-time 2 http://localhost:15672 >nul 2>&1
if errorlevel 1 (
    echo [X] RabbitMQ is DOWN
) else (
    echo [+] RabbitMQ is UP
)

echo.
echo [*] Resource Usage:
echo.
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo.
echo [i] Run 'logs.bat [service]' to view logs for a specific service
echo.
pause
