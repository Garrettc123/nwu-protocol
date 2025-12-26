@echo off
REM Log Viewer Script for Windows

color 0E

if "%1"=="" (
    echo [*] Showing logs for all services...
    echo.
    echo Press Ctrl+C to stop
    echo.
    docker-compose logs -f --tail=50
) else (
    echo [*] Showing logs for: %1
    echo.
    echo Press Ctrl+C to stop
    echo.
    docker-compose logs -f --tail=100 %1
)
