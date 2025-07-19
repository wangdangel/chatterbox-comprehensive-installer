@echo off
echo Setting up GitHub connection for ChatterBox TTS...
echo.

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

REM Check current status
echo Current git status:
git status
echo.

REM Check remote
echo Current remote configuration:
git remote -v
echo.

echo To complete the setup:
echo 1. Create the repository on GitHub: https://github.com/new
echo 2. Repository name: chatterbox-comprehensive-installer
echo 3. Don't initialize with README (we already have one)
echo 4. Run: git push -u origin main
echo.

pause