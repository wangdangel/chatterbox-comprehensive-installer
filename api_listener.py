#!/usr/bin/env python3
"""
Lightweight FastAPI server for Chatterbox TTS
Simplified version focusing on core TTS functionality
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chatterbox_tts.core.processor import TTSProcessor
from chatterbox_tts.core.config import config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize processor
processor = TTSProcessor()

# Pydantic models
class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    voice_id: str = Field(default="microsoft_speecht5", description="Voice ID to use")
    speed: Optional[float] = Field(default=1.0, ge=0.1, le=3.0)
    pitch: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)

class TTSResponse(BaseModel):
    success: bool
    audio_url: str
    filename: str
    duration: float
    file_size: int

# Initialize FastAPI
app = FastAPI(
    title="Chatterbox TTS",
    description="Simple TTS API using chatterbox-tts",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chatterbox TTS API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check."""
    return {"status": "healthy"}

@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest,
    background_tasks: BackgroundTasks
):
    """Convert text to speech."""
    try:
        # Validate input
        is_valid, message = processor.validate_input(request.text)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Process text
        audio_path = await processor.process_text(
            text=request.text,
            voice_id=request.voice_id,
            speed=request.speed,
            pitch=request.pitch
        )
        
        # Get file info
        file_path = Path(audio_path)
        file_size = file_path.stat().st_size
        
        # Get duration
        try:
            import librosa
            audio_data, sr = librosa.load(audio_path)
            duration = len(audio_data) / sr
        except ImportError:
            duration = 0.0
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_file, audio_path)
        
        return TTSResponse(
            success=True,
            audio_url=f"/audio/{file_path.name}",
            filename=file_path.name,
            duration=duration,
            file_size=file_size
        )
        
    except Exception as e:
        logger.error(f"TTS processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts/file")
async def file_to_speech(
    file: UploadFile = File(...),
    voice_id: str = Form(default="microsoft_speecht5"),
    speed: Optional[float] = Form(default=1.0),
    pitch: Optional[float] = Form(default=1.0),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Convert uploaded file to speech."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Save uploaded file
        import tempfile
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".txt",
            dir=config_manager.get_path("processing", "temp")
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process file
        audio_path = await processor.process_file(
            file_path=temp_file_path,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch
        )
        
        # Get file info
        file_path = Path(audio_path)
        file_size = file_path.stat().st_size
        
        # Get duration
        try:
            import librosa
            audio_data, sr = librosa.load(audio_path)
            duration = len(audio_data) / sr
        except ImportError:
            duration = 0.0
        
        # Cleanup
        background_tasks.add_task(cleanup_file, temp_file_path)
        background_tasks.add_task(cleanup_file, audio_path)
        
        return TTSResponse(
            success=True,
            audio_url=f"/audio/{file_path.name}",
            filename=file_path.name,
            duration=duration,
            file_size=file_size
        )
        
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files."""
    audio_dir = Path(config_manager.get_path("processing", "output"))
    file_path = audio_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(file_path, media_type="audio/wav")

@app.get("/voices")
async def list_voices():
    """List available voices."""
    try:
        from chatterbox_tts.core.voice_manager import voice_manager
        voices = voice_manager.list_voices()
        return [{"id": v.id, "name": v.name, "description": v.description} for v in voices]
    except Exception as e:
        logger.error(f"Failed to list voices: {e}")
        return [{"id": "microsoft_speecht5", "name": "Microsoft SpeechT5", "description": "Default voice"}]

def cleanup_file(file_path: str):
    """Clean up file after serving."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass

def load_config():
    """Load configuration from JSON file."""
    config_file = Path.home() / ".chatterbox_tts" / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    return {"server": {"host": "0.0.0.0", "port": 2049}}

if __name__ == "__main__":
    config = load_config()
    server_config = config.get("server", {})
    
    uvicorn.run(
        app,
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 2049),
        log_level="info"
    )