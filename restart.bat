@echo off
REM Restart All Services

color 0D
echo.
echo [*] Restarting all services...
echo.

if "%1"=="" (
    docker-compose restart
) else (
    echo [*] Restarting: %1
    docker-compose restart %1
)

echo.
echo [+] Services restarted
echo.
echo [i] Run 'status.bat' to check health
echo.
pause
