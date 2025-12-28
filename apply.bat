@echo off
REM NWU Protocol - Apply/Submit Contribution Tool (Windows)

setlocal enabledelayedexpansion

if not defined API_URL set API_URL=http://localhost:8000

echo ================================================================
echo          NWU Protocol - Submit Your Contribution
echo ================================================================
echo.

REM Check if curl is available
where curl >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: curl is not installed or not in PATH
    echo Please install curl or use Git Bash to run apply.sh
    exit /b 1
)

REM Check if API is running
curl -s --max-time 2 "%API_URL%/health" >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: NWU Protocol API is not running
    echo.
    echo Please start the services first:
    echo   setup.bat    # First time setup
    echo   status.bat   # Check service status
    echo.
    exit /b 1
)

REM Show help if requested
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="/?" goto :show_help

REM Check arguments
if "%1"=="" goto :interactive_mode

REM Command-line mode
set type=%1
set file=%2
set title=%3
set description=%4

if "%type%"=="" (
    echo Error: Missing contribution type
    goto :show_help
)

if "%file%"=="" (
    echo Error: Missing file path
    goto :show_help
)

if not exist "%file%" (
    echo Error: File not found: %file%
    exit /b 1
)

if "%title%"=="" set title=Untitled Contribution
if "%description%"=="" set description=No description provided

echo Submitting contribution...
echo.

curl -X POST "%API_URL%/api/v1/contributions" ^
    -F "file=@%file%" ^
    -F "type=%type%" ^
    -F "title=%title%" ^
    -F "description=%description%"

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo   Contribution submitted successfully!
    echo ================================================================
    echo.
    echo Next Steps:
    echo   1. Your contribution is being verified by AI agents
    echo   2. Check status at: %API_URL%/api/v1/contributions/^<id^>
    echo   3. View dashboard at: http://localhost:3000/dashboard
    echo   4. Verification typically takes 2-5 minutes
    echo.
) else (
    echo.
    echo Error: Failed to submit contribution
    exit /b 1
)

exit /b 0

:interactive_mode
echo Interactive Submission Mode
echo.
echo Contribution Types:
echo   1. Code        - Source code, libraries, algorithms
echo   2. Dataset     - Training data, research datasets
echo   3. Document    - Research papers, documentation
echo   4. Model       - AI/ML models, pre-trained weights
echo.

set /p type_choice="Select contribution type (1-4): "

if "%type_choice%"=="1" set type=code
if "%type_choice%"=="2" set type=dataset
if "%type_choice%"=="3" set type=document
if "%type_choice%"=="4" set type=model

if not defined type (
    echo Invalid choice. Using 'code' as default.
    set type=code
)

echo.
set /p file="Enter file or directory path: "

if not exist "%file%" (
    echo Error: File or directory not found: %file%
    exit /b 1
)

set /p title="Enter contribution title: "

echo Enter description (press Enter to finish):
set /p description=""

echo.
echo ================================================================
echo Submission Summary:
echo ================================================================
echo   Type:        %type%
echo   File:        %file%
echo   Title:       %title%
echo   Description: %description%
echo.

set /p confirm="Submit this contribution? (y/n): "

if /i not "%confirm%"=="y" (
    echo Submission cancelled.
    exit /b 0
)

echo.
echo Submitting contribution...

curl -X POST "%API_URL%/api/v1/contributions" ^
    -F "file=@%file%" ^
    -F "type=%type%" ^
    -F "title=%title%" ^
    -F "description=%description%"

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo   Contribution submitted successfully!
    echo ================================================================
    echo.
    echo Next Steps:
    echo   1. Your contribution is being verified by AI agents
    echo   2. Check status at: %API_URL%/api/v1/contributions/^<id^>
    echo   3. View dashboard at: http://localhost:3000/dashboard
    echo   4. Verification typically takes 2-5 minutes
    echo.
) else (
    echo.
    echo Error: Failed to submit contribution
    exit /b 1
)

exit /b 0

:show_help
echo.
echo NWU Protocol - Apply/Submit Contribution Tool
echo.
echo USAGE:
echo   apply.bat                                 # Interactive mode
echo   apply.bat ^<type^> ^<file^> ^<title^> [desc]    # Command-line mode
echo   apply.bat --help                          # Show this help
echo.
echo EXAMPLES:
echo   # Interactive mode
echo   apply.bat
echo.
echo   # Submit code
echo   apply.bat code ./my-algorithm.py "ML Algorithm" "Description here"
echo.
echo   # Submit dataset
echo   apply.bat dataset ./data.csv "Training Data"
echo.
echo   # Submit document
echo   apply.bat document ./research.pdf "Research Paper"
echo.
echo CONTRIBUTION TYPES:
echo   code      - Source code, libraries, algorithms
echo   dataset   - Training data, research datasets
echo   document  - Research papers, documentation
echo   model     - AI/ML models, pre-trained weights
echo.
echo ENVIRONMENT VARIABLES:
echo   API_URL   - Override API endpoint (default: http://localhost:8000)
echo.
echo MORE INFO:
echo   Documentation: README.md
echo   Dashboard:     http://localhost:3000
echo   API Docs:      http://localhost:8000/docs
echo.
exit /b 0
