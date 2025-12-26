@echo off
REM Stop All Services

color 0C
echo.
echo [*] Stopping all NWU Protocol services...
echo.

docker-compose down

echo.
echo [+] All services stopped
echo.
echo [i] Data is preserved. Run 'setup.bat' to restart
echo.
pause
