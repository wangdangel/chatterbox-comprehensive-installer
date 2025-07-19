#!/bin/bash

# Chatterbox TTS Batch Processing System Setup Script
# This script automates the complete setup of the TTS batch processing system

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to handle errors
handle_error() {
    print_error "An error occurred on line $1"
    print_error "Setup failed. Please check the error messages above."
    exit 1
}

# Set trap for error handling
trap 'handle_error $LINENO' ERR

# Welcome message
echo "=========================================="
echo "  Chatterbox TTS Batch Processing Setup"
echo "=========================================="
echo

# Check if Python 3.8+ is available
print_status "Checking Python version..."
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_error "Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required."
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# Create root directory
ROOT_DIR="chatterbox_batch_processor"
print_status "Creating project directory: $ROOT_DIR..."
if [ -d "$ROOT_DIR" ]; then
    print_warning "Directory $ROOT_DIR already exists. Removing old directory..."
    rm -rf "$ROOT_DIR"
fi
mkdir -p "$ROOT_DIR"
cd "$ROOT_DIR"

# Create job directories
print_status "Creating job directories..."
mkdir -p _jobs_input_dir
mkdir -p _jobs_output_dir
print_success "Job directories created"

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate  # Windows compatibility

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install required packages
print_status "Installing required Python packages..."

# Try CUDA version of PyTorch first
print_status "Attempting to install PyTorch with CUDA support..."
if pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118; then
    print_success "PyTorch with CUDA support installed successfully"
else
    print_warning "CUDA version failed, falling back to CPU-only version..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    print_success "PyTorch CPU-only version installed"
fi

# Install other required packages
print_status "Installing additional packages..."
pip install transformers
pip install fastapi
pip install uvicorn
pip install pydantic
pip install python-multipart
pip install soundfile
pip install numpy
pip install requests
pip install tqdm

print_success "All packages installed successfully"

# Create api_listener.py
print_status "Creating api_listener.py..."
cat > api_listener.py << 'EOF'
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
import json
import shutil
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatterbox TTS Batch Processor API", version="1.0.0")

# Directory paths
JOBS_INPUT_DIR = Path("_jobs_input_dir")
JOBS_OUTPUT_DIR = Path("_jobs_output_dir")
JOBS_INPUT_DIR.mkdir(exist_ok=True)
JOBS_OUTPUT_DIR.mkdir(exist_ok=True)

# Job tracking
class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    created_at: datetime
    completed_at: datetime = None
    input_filename: str
    output_filename: str = None
    error_message: str = None

# In-memory job storage (in production, use a database)
jobs = {}

@app.get("/")
async def root():
    return {"message": "Chatterbox TTS Batch Processor API is running"}

@app.post("/submit-job")
async def submit_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Submit a new TTS job by uploading a text file."""
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    
    job_id = str(uuid.uuid4())
    input_filename = f"{job_id}_{file.filename}"
    input_path = JOBS_INPUT_DIR / input_filename
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create job record
        job = JobStatus(
            job_id=job_id,
            status="pending",
            created_at=datetime.now(),
            input_filename=input_filename
        )
        jobs[job_id] = job
        
        # Add background task to process the job
        background_tasks.add_task(process_tts_job, job_id)
        
        logger.info(f"Job {job_id} submitted successfully")
        return {"job_id": job_id, "status": "pending"}
        
    except Exception as e:
        logger.error(f"Error submitting job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a specific job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "input_filename": job.input_filename,
        "output_filename": job.output_filename,
        "error_message": job.error_message
    }

@app.get("/download-result/{job_id}")
async def download_result(job_id: str):
    """Download the completed audio file for a job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    output_path = JOBS_OUTPUT_DIR / job.output_filename
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        path=output_path,
        filename=job.output_filename,
        media_type="audio/wav"
    )

@app.get("/list-jobs")
async def list_jobs():
    """List all jobs with their current status."""
    return [
        {
            "job_id": job.job_id,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "input_filename": job.input_filename
        }
        for job in jobs.values()
    ]

def process_tts_job(job_id: str):
    """Process a TTS job (called in background)."""
    try:
        job = jobs[job_id]
        job.status = "processing"
        logger.info(f"Starting processing for job {job_id}")
        
        # Import here to avoid circular imports
        from tts_processor_script import process_text_file
        
        # Process the file
        input_path = JOBS_INPUT_DIR / job.input_filename
        output_filename = f"{job_id}_output.wav"
        output_path = JOBS_OUTPUT_DIR / output_filename
        
        success = process_text_file(str(input_path), str(output_path))
        
        if success:
            job.status = "completed"
            job.completed_at = datetime.now()
            job.output_filename = output_filename
            logger.info(f"Job {job_id} completed successfully")
        else:
            job.status = "failed"
            job.error_message = "Processing failed"
            logger.error(f"Job {job_id} failed during processing")
            
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        logger.error(f"Job {job_id} failed with error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2049)
EOF

print_success "api_listener.py created"

# Create tts_processor_script.py
print_status "Creating tts_processor_script.py..."
cat > tts_processor_script.py << 'EOF'
import torch
from transformers import AutoTokenizer, AutoModelForTextToWaveform
import soundfile as sf
import logging
import os
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSProcessor:
    def __init__(self):
        self.model_name = "microsoft/speecht5_tts"
        self.vocoder_name = "microsoft/speecht5_hifigan"
        self.tokenizer = None
        self.model = None
        self.vocoder = None
        self.speaker_embeddings = None
        
    def load_model(self):
        """Load the TTS model and vocoder."""
        try:
            logger.info("Loading TTS model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTextToWaveform.from_pretrained(self.model_name)
            self.vocoder = AutoModelForTextToWaveform.from_pretrained(self.vocoder_name)
            
            # Load speaker embeddings (using a default speaker)
            from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
            processor = SpeechT5Processor.from_pretrained(self.model_name)
            model = SpeechT5ForTextToSpeech.from_pretrained(self.model_name)
            vocoder = SpeechT5HifiGan.from_pretrained(self.vocoder_name)
            
            # Use a default speaker embedding (this is a simplified approach)
            # In production, you might want to use specific speaker embeddings
            self.speaker_embeddings = torch.randn(1, 512)  # Placeholder
            
            logger.info("TTS model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading TTS model: {str(e)}")
            return False
    
    def preprocess_text(self, text):
        """Preprocess text for TTS processing."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split into sentences for better processing
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def text_to_speech(self, text, output_path):
        """Convert text to speech and save as audio file."""
        try:
            if not self.model:
                if not self.load_model():
                    return False
            
            sentences = self.preprocess_text(text)
            audio_segments = []
            
            for sentence in sentences:
                if len(sentence) > 0:
                    # Tokenize input
                    inputs = self.tokenizer(sentence, return_tensors="pt")
                    
                    # Generate speech
                    with torch.no_grad():
                        # This is a simplified version - adjust based on your specific model
                        speech = self.model.generate_speech(
                            inputs["input_ids"],
                            speaker_embeddings=self.speaker_embeddings,
                            vocoder=self.vocoder
                        )
                    
                    audio_segments.append(speech.squeeze().cpu().numpy())
            
            if audio_segments:
                # Concatenate all audio segments
                import numpy as np
                final_audio = np.concatenate(audio_segments)
                
                # Save to file
                sf.write(output_path, final_audio, samplerate=16000)
                logger.info(f"Audio saved to {output_path}")
                return True
            else:
                logger.warning("No audio generated - empty text")
                return False
                
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {str(e)}")
            return False

def process_text_file(input_path, output_path):
    """Process a text file and generate audio."""
    try:
        processor = TTSProcessor()
        
        # Read input text
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            logger.error("Input file is empty")
            return False
        
        # Generate speech
        success = processor.text_to_speech(text, output_path)
        
        if success:
            logger.info(f"Successfully processed {input_path} -> {output_path}")
            return True
        else:
            logger.error("Failed to process text file")
            return False
            
    except Exception as e:
        logger.error(f"Error processing text file: {str(e)}")
        return False

# Alternative implementation using a simpler TTS model
class SimpleTTSProcessor:
    def __init__(self):
        self.model = None
        
    def load_model(self):
        """Load a simpler TTS model for fallback."""
        try:
            from transformers import pipeline
            self.model = pipeline("text-to-speech", model="suno/bark-small")
            logger.info("Simple TTS model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading simple TTS model: {str(e)}")
            return False
    
    def text_to_speech_simple(self, text, output_path):
        """Convert text to speech using simpler model."""
        try:
            if not self.model:
                if not self.load_model():
                    return False
            
            # Generate speech
            speech = self.model(text)
            
            # Save to file
            import scipy.io.wavfile as wavfile
            wavfile.write(output_path, rate=speech["sampling_rate"], data=speech["audio"])
            
            logger.info(f"Audio saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error in simple TTS conversion: {str(e)}")
            return False

# Main processing function with fallback
def process_text_file(input_path, output_path):
    """Process a text file with fallback to simpler model."""
    try:
        # Try primary processor
        processor = TTSProcessor()
        if processor.load_model():
            logger.info("Using primary TTS processor")
            return processor.text_to_speech(input_path, output_path)
        
        # Fallback to simple processor
        logger.warning("Primary processor failed, trying simple processor")
        simple_processor = SimpleTTSProcessor()
        if simple_processor.load_model():
            logger.info("Using simple TTS processor")
            return simple_processor.text_to_speech_simple(input_path, output_path)
        
        logger.error("All TTS processors failed")
        return False
        
    except Exception as e:
        logger.error(f"Error in process_text_file: {str(e)}")
        return False

# For direct script execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python tts_processor_script.py <input_file.txt> <output_file.wav>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if process_text_file(input_file, output_file):
        print("Processing completed successfully")
    else:
        print("Processing failed")
        sys.exit(1)
EOF

print_success "tts_processor_script.py created"

# Set file permissions (Unix-like systems)
print_status "Setting file permissions..."
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    chmod +x api_listener.py
    chmod +x tts_processor_script.py
    print_success "File permissions set"
else
    print_warning "Skipping file permissions (Windows detected)"
fi

# Create requirements.txt for reference
print_status "Creating requirements.txt..."
pip freeze > requirements.txt
print_success "requirements.txt created"

# Create README.md with instructions
print_status "Creating README.md..."
cat > README.md << 'EOF'
# Chatterbox TTS Batch Processing System

## Overview
This system provides a complete TTS (Text-to-Speech) batch processing solution with a FastAPI web interface and background job processing.

## Directory Structure
```
chatterbox_batch_processor/
├── venv/                    # Python virtual environment
├── _jobs_input_dir/         # Input text files directory
├── _jobs_output_dir/        # Output audio files