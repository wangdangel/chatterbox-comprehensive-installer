@echo off
REM Windows startup script for Chatterbox TTS

echo Starting Chatterbox TTS Server...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Run 'python simple_install.py' first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate

REM Check if api_listener.py exists
if not exist "api_listener.py" (
    echo api_listener.py not found. Please check your installation.
    pause
    exit /b 1
)

REM Start the server
python api_listener.py

pause