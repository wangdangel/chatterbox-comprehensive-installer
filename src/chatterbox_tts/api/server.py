"""
FastAPI server for Chatterbox TTS.
Provides REST API endpoints for TTS processing.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ..core.config import config_manager
from ..core.voice_manager import voice_manager
from ..core.processor import tts_processor
from ..core.document_parser import DocumentParser

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Chatterbox TTS API",
    description="Text-to-Speech API with multiple voices and advanced features",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class TTSRequest(BaseModel):
    """Request model for TTS processing."""
    text: str = Field(..., description="Text to convert to speech")
    voice_id: str = Field(default="default", description="Voice ID to use")
    speed: Optional[float] = Field(default=None, ge=0.1, le=3.0, description="Speech speed multiplier")
    pitch: Optional[float] = Field(default=None, ge=0.5, le=2.0, description="Pitch multiplier")
    stitch_audio: bool = Field(default=True, description="Whether to stitch audio segments")


class TTSResponse(BaseModel):
    """Response model for TTS processing."""
    success: bool
    audio_url: str
    filename: str
    duration: float
    file_size: int
    metadata: Dict[str, Any]


class VoiceInfoResponse(BaseModel):
    """Response model for voice information."""
    id: str
    name: str
    description: str
    language: str
    gender: str
    is_default: bool
    is_downloaded: bool
    file_size: Optional[int] = None


class ProcessingEstimate(BaseModel):
    """Response model for processing estimates."""
    character_count: int
    estimated_segments: int
    estimated_processing_time_seconds: float
    estimated_file_size_mb: float


class DocumentAnalysis(BaseModel):
    """Response model for document analysis."""
    filename: str
    total_chars: int
    total_segments: int
    estimated_processing_time: float
    requires_stitching: bool
    analysis: Dict[str, Any]


# Global variables
document_parser = DocumentParser()
temp_files: Dict[str, str] = {}  # Track temporary files for cleanup


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
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/voices", response_model=List[VoiceInfoResponse])
async def list_voices():
    """List all available voices."""
    voices = voice_manager.list_voices()
    return [
        VoiceInfoResponse(
            id=voice.id,
            name=voice.name,
            description=voice.description,
            language=voice.language,
            gender=voice.gender,
            is_default=voice.is_default,
            is_downloaded=voice.is_downloaded,
            file_size=voice.file_size
        )
        for voice in voices
    ]


@app.get("/voices/{voice_id}")
async def get_voice(voice_id: str):
    """Get specific voice information."""
    voice_config = voice_manager.get_voice(voice_id)
    if not voice_config:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    return voice_config


@app.post("/voices/{voice_id}/set-default")
async def set_default_voice(voice_id: str):
    """Set a voice as default."""
    success = voice_manager.set_default_voice(voice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    return {"success": True, "message": f"Set {voice_id} as default voice"}


@app.post("/tts/text", response_model=TTSResponse)
async def tts_from_text(request: TTSRequest, background_tasks: BackgroundTasks):
    """Convert text to speech."""
    try:
        # Validate input
        is_valid, message = tts_processor.validate_input(request.text)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Process text
        audio_path = await tts_processor.process_text(
            text=request.text,
            voice_id=request.voice_id,
            speed=request.speed,
            pitch=request.pitch,
            stitch_audio=request.stitch_audio
        )
        
        # Get file info
        file_path = Path(audio_path)
        file_size = file_path.stat().st_size
        
        # Load audio to get duration
        import librosa
        audio_data, sr = librosa.load(audio_path)
        duration = len(audio_data) / sr
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, audio_path)
        
        return TTSResponse(
            success=True,
            audio_url=f"/audio/{file_path.name}",
            filename=file_path.name,
            duration=duration,
            file_size=file_size,
            metadata={
                "voice_id": request.voice_id,
                "speed": request.speed,
                "pitch": request.pitch,
                "segments": 1
            }
        )
        
    except Exception as e:
        logger.error(f"TTS processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/file")
async def tts_from_file(
    file: UploadFile = File(...),
    voice_id: str = Form(default="default"),
    speed: Optional[float] = Form(default=None),
    pitch: Optional[float] = Form(default=None),
    stitch_audio: bool = Form(default=True),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Convert file to speech."""
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = Path(file.filename).suffix.lower()
        supported_extensions = tts_processor.get_supported_formats()
        
        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: {supported_extensions}"
            )
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension,
            dir=config_manager.get_path("processing", "temp")
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process file
        audio_path = await tts_processor.process_file(
            file_path=temp_file_path,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch,
            stitch_audio=stitch_audio
        )
        
        # Get file info
        file_path = Path(audio_path)
        file_size = file_path.stat().st_size
        
        # Load audio to get duration
        import librosa
        audio_data, sr = librosa.load(audio_path)
        duration = len(audio_data) / sr
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, temp_file_path)
        background_tasks.add_task(cleanup_temp_file, audio_path)
        
        return TTSResponse(
            success=True,
            audio_url=f"/audio/{file_path.name}",
            filename=file_path.name,
            duration=duration,
            file_size=file_size,
            metadata={
                "original_filename": file.filename,
                "voice_id": voice_id,
                "speed": speed,
                "pitch": pitch
            }
        )
        
    except Exception as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts/estimate")
async def get_processing_estimate(request: TTSRequest):
    """Get processing time estimate for text."""
    try:
        estimate = await tts_processor.get_processing_estimate(request.text)
        return ProcessingEstimate(**estimate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    """Analyze uploaded file."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(file.filename).suffix.lower(),
            dir=config_manager.get_path("processing", "temp")
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Analyze document
        document = document_parser.parse_file(temp_file_path)
        analysis = document_parser.create_processing_plan(document)
        
        # Clean up
        try:
            os.remove(temp_file_path)
        except OSError:
            pass
        
        return DocumentAnalysis(**analysis)
        
    except Exception as e:
        logger.error(f"File analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files."""
    audio_dir = Path(config_manager.get_path("processing", "output"))
    file_path = audio_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(file_path, media_type="audio/wav")


@app.get("/status")
async def get_status():
    """Get system status."""
    return {
        "status": "running",
        "config": {
            "host": config_manager.config.server.host,
            "port": config_manager.config.server.port,
            "log_level": config_manager.config.server.log_level
        },
        "voices": len(voice_manager.list_voices()),
        "processing": tts_processor.get_processing_status()
    }


@app.delete("/cleanup")
async def cleanup_temp_files():
    """Clean up temporary files."""
    try:
        temp_dir = Path(config_manager.get_path("processing", "temp"))
        output_dir = Path(config_manager.get_path("processing", "output"))
        
        # Clean temp directory
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                try:
                    file_path.unlink()
                except OSError:
                    pass
        
        # Clean old output files (older than 1 hour)
        import time
        current_time = time.time()
        for file_path in output_dir.glob("*.wav"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > 3600:  # 1 hour
                    try:
                        file_path.unlink()
                    except OSError:
                        pass
        
        return {"success": True, "message": "Cleanup completed"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def cleanup_temp_file(file_path: str):
    """Clean up temporary file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=config_manager.config.server.host,
        port=config_manager.config.server.port,
        reload=config_manager.config.server.reload,
        log_level=config_manager.config.server.log_level.lower()
    )