@echo off
REM Help and Documentation

color 0B
cls

echo ========================================================
echo              NWU Protocol - Quick Reference
echo ========================================================
echo.
echo GETTING STARTED
echo --------------------------------------------------------
echo   setup.bat              One-command setup (first time)
echo   status.bat             Check all services
echo   logs.bat [service]     View logs (all or specific)
echo   apply.bat              Submit a contribution (interactive)
echo.
echo MANAGEMENT
echo --------------------------------------------------------
echo   stop.bat               Stop all services (keeps data)
echo   restart.bat [service]  Restart all or specific service
echo.
echo SERVICE URLS
echo --------------------------------------------------------
echo   Frontend:       http://localhost:3000
echo   Backend API:    http://localhost:8000
echo   API Docs:       http://localhost:8000/docs
echo   RabbitMQ:       http://localhost:15672 (guest/guest)
echo   PostgreSQL:     localhost:5432
echo   Redis:          localhost:6379
echo   IPFS:           http://localhost:5001
echo.
echo DOCKER COMMANDS
echo --------------------------------------------------------
echo   docker-compose ps                      List containers
echo   docker-compose logs -f backend         Follow backend logs
echo   docker-compose exec backend bash       Enter backend shell
echo   docker-compose restart agent-alpha     Restart service
echo.
echo TROUBLESHOOTING
echo --------------------------------------------------------
echo   1. Services won't start?
 echo      - Check: docker-compose logs
echo      - Verify: .env file has OPENAI_API_KEY
echo.
echo   2. Port already in use?
echo      - Check: netstat -ano ^| findstr :3000
echo      - Stop: taskkill /PID [PID] /F
echo.
echo   3. Out of disk space?
echo      - Clean: docker system prune -a
echo.
echo DOCUMENTATION
echo --------------------------------------------------------
echo   README.md          Full project documentation
echo   EASY_START.md      Simple setup guide
echo   QUICKSTART.md      Quick setup guide
echo   SETUP_GUIDE.md     Detailed instructions
echo.
echo ========================================================
echo Need more help? Check the docs or open an issue on GitHub
echo ========================================================
echo.
pause
