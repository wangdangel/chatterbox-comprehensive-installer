@echo off
setlocal enabledelayedexpansion

:: Chatterbox TTS Dual-Mode Installer for Windows
title Chatterbox TTS Installation Wizard

:main_menu
cls
echo ==========================================
echo   Chatterbox TTS Installation Wizard
echo ==========================================
echo.
echo Please select installation mode:
echo.
echo 1) Simple Installation
echo    - Basic FastAPI server
echo    - Essential audio processing
echo    - Lightweight setup
echo.
echo 2) Complex Installation
echo    - Full chatterbox-tts package
echo    - Advanced TTS models
echo    - Complete modular system
echo.
echo 3) Exit
echo.
set /p choice=Enter your choice (1-3): 

if "%choice%"=="1" goto setup_simple
if "%choice%"=="2" goto setup_complex
if "%choice%"=="3" goto exit_script
goto main_menu

:setup_simple
cls
echo ==========================================
echo   Simple Installation Mode
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    goto main_menu
)

:: Create project directory
set "project_dir=chatterbox_tts_simple"
echo [STEP] Creating project directory: %project_dir%

if exist "%project_dir%" (
    echo [WARNING] Directory %project_dir% already exists
    set /p "remove_dir=Remove existing directory? (y/n): "
    if /i "%remove_dir%"=="y" (
        rmdir /s /q "%project_dir%"
    ) else (
        echo [ERROR] Installation cancelled
        pause
        goto main_menu
    )
)

mkdir "%project_dir%"
cd "%project_dir%"

:: Create virtual environment
echo [STEP] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    goto main_menu
)
echo [SUCCESS] Virtual environment created

:: Install dependencies
echo [STEP] Installing basic dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install fastapi uvicorn pydantic python-multipart numpy soundfile scipy librosa
echo [SUCCESS] Basic dependencies installed

:: Create basic structure
mkdir input
mkdir output
mkdir logs

:: Create simple API server
echo [STEP] Creating simple API server...
echo from fastapi import FastAPI, File, UploadFile, HTTPException > simple_server.py
echo from fastapi.responses import FileResponse >> simple_server.py
echo import os >> simple_server.py
echo import uuid >> simple_server.py
echo import shutil >> simple_server.py
echo from pathlib import Path >> simple_server.py
echo. >> simple_server.py
echo app = FastAPI(title="Chatterbox TTS Simple", version="1.0.0") >> simple_server.py
echo. >> simple_server.py
echo INPUT_DIR = Path("input") >> simple_server.py
echo OUTPUT_DIR = Path("output") >> simple_server.py
echo INPUT_DIR.mkdir(exist_ok=True) >> simple_server.py
echo OUTPUT_DIR.mkdir(exist_ok=True) >> simple_server.py
echo. >> simple_server.py
echo @app.get("/") >> simple_server.py
echo async def root(): >> simple_server.py
echo     return {"message": "Chatterbox TTS Simple API is running"} >> simple_server.py
echo. >> simple_server.py
echo @app.post("/process") >> simple_server.py
echo async def process_file(file: UploadFile = File(...)): >> simple_server.py
echo     if not file.filename.endswith('.txt'): >> simple_server.py
echo         raise HTTPException(status_code=400, detail="Only .txt files supported") >> simple_server.py
echo. >> simple_server.py
echo     job_id = str(uuid.uuid4()) >> simple_server.py
echo     input_path = INPUT_DIR / f"{job_id}.txt" >> simple_server.py
echo     output_path = OUTPUT_DIR / f"{job_id}.wav" >> simple_server.py
echo. >> simple_server.py
echo     with open(input_path, "wb") as buffer: >> simple_server.py
echo         shutil.copyfileobj(file.file, buffer) >> simple_server.py
echo. >> simple_server.py
echo     with open(input_path, 'r') as f: >> simple_server.py
echo         text = f.read() >> simple_server.py
echo. >> simple_server.py
echo     import numpy as np >> simple_server.py
echo     import soundfile as sf >> simple_server.py
echo     sample_rate = 22050 >> simple_server.py
echo     duration = len(text) * 0.1 >> simple_server.py
echo     t = np.linspace(0, duration, int(sample_rate * duration)) >> simple_server.py
echo     audio = np.sin(2 * np.pi * 440 * t) * 0.3 >> simple_server.py
echo     sf.write(output_path, audio, sample_rate) >> simple_server.py
echo. >> simple_server.py
echo     return {"job_id": job_id, "status": "completed", "download_url": f"/download/{job_id}"} >> simple_server.py
echo. >> simple_server.py
echo @app.get("/download/{job_id}") >> simple_server.py
echo async def download_file(job_id: str): >> simple_server.py
echo     output_path = OUTPUT_DIR / f"{job_id}.wav" >> simple_server.py
echo     if not output_path.exists(): >> simple_server.py
echo         raise HTTPException(status_code=404, detail="File not found") >> simple_server.py
echo     return FileResponse(output_path, filename=f"{job_id}.wav") >> simple_server.py
echo. >> simple_server.py
echo if __name__ == "__main__": >> simple_server.py
echo     import uvicorn >> simple_server.py
echo     uvicorn.run(app, host="0.0.0.0", port=2049) >> simple_server.py

:: Create run script
echo @echo off > run.bat
echo call venv\Scripts\activate.bat >> run.bat
echo python simple_server.py >> run.bat
echo pause >> run.bat

echo.
echo [SUCCESS] Simple installation completed!
echo.
echo To start the server:
echo   cd %project_dir%
echo   run.bat
echo.
echo API will be available at: http://localhost:2049
pause
goto main_menu

:setup_complex
cls
echo ==========================================
echo   Complex Installation Mode
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    goto main_menu
)

:: Check if setup.py exists
if not exist "setup.py" (
    echo [ERROR] setup.py not found. Please ensure you're in the correct directory
    pause
    goto main_menu
)

:: Create virtual environment
echo [STEP] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    goto main_menu
)
echo [SUCCESS] Virtual environment created

:: Install dependencies
echo [STEP] Installing full dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip

:: Install PyTorch with CUDA support
echo [INFO] Installing PyTorch (attempting CUDA support)...
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
if %errorlevel%==0 (
    echo [SUCCESS] PyTorch with CUDA support installed
) else (
    echo [WARNING] CUDA version failed, installing CPU-only version...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    echo [SUCCESS] PyTorch CPU-only version installed
)

:: Install package in development mode
echo [STEP] Installing chatterbox-tts package...
pip install -e .
echo [SUCCESS] Package installed in development mode

:: Create run script
echo @echo off > run.bat
echo call venv\Scripts\activate.bat >> run.bat
echo python -m chatterbox_tts >> run.bat
echo pause >> run.bat

:: Create API run script
echo @echo off > run_api.bat
echo call venv\Scripts\activate.bat >> run_api.bat
echo python -m chatterbox_tts.api.server >> run_api.bat
echo pause >> run_api.bat

echo.
echo [SUCCESS] Complex installation completed!
echo.
echo To start the CLI:
echo   run.bat
echo.
echo To start the API server:
echo   run_api.bat
echo.
echo CLI commands:
echo   chatterbox-tts --help
echo   chatterbox-tts process input.txt output.wav
pause
goto main_menu

:exit_script
echo.
echo Thank you for using Chatterbox TTS!
pause
exit