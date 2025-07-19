# Chatterbox TTS - Simplified Setup

This is a streamlined version of Chatterbox TTS that focuses on essential functionality without the complex modular structure.

## Quick Start

### 1. Run the Simple Installer
```bash
python simple_install.py
```

This will:
- Check Python version compatibility
- Detect GPU availability
- Create virtual environment
- Install dependencies
- Set up directories and configuration
- Create startup scripts

### 2. Start the Server
After installation, you can start the API server:

**Windows:**
```bash
run_server.bat
```

**Linux/Mac:**
```bash
./run_server.sh
```

Or manually:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
python api_listener.py
```

The server will start on `http://localhost:2049`

### 3. Use the API

#### Convert Text to Speech
```bash
curl -X POST "http://localhost:2049/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test.", "voice_id": "microsoft_speecht5"}'
```

#### Convert File to Speech
```bash
curl -X POST "http://localhost:2049/tts/file" \
  -F "file=@input.txt" \
  -F "voice_id=microsoft_speecht5"
```

### 4. Use the Worker Script

#### Process Text
```bash
python tts_processor.py --text "Hello world" --output hello.wav
```

#### Process File
```bash
python tts_processor.py --file input.txt --output output.wav
```

#### List Voices
```bash
python tts_processor.py --list-voices
```

#### Get Processing Estimate
```bash
python tts_processor.py --text "Your text here" --estimate
```

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /tts` - Convert text to speech
- `POST /tts/file` - Convert file to speech
- `GET /audio/{filename}` - Download audio file
- `GET /voices` - List available voices

## Configuration

Configuration is stored in `~/.chatterbox_tts/config.json`

Default directories:
- Input: `~/.chatterbox_tts/input/`
- Output: `~/.chatterbox_tts/output/`
- Temp: `~/.chatterbox_tts/temp/`
- Logs: `~/.chatterbox_tts/logs/`

## Dependencies

The simplified setup uses the same requirements as the main project but focuses on:
- FastAPI for the web server
- Core TTS processing
- Essential audio handling

## Troubleshooting

1. **Import errors**: Ensure virtual environment is activated
2. **Audio generation fails**: Check if models are downloaded
3. **Port conflicts**: Change port in `~/.chatterbox_tts/config.json`

## Files Created

- `simple_install.py` - Automated installer
- `api_listener.py` - Lightweight FastAPI server
- `tts_processor.py` - Command-line TTS processor
- `run_server.bat` / `run_server.sh` - Startup scripts
- `~/.chatterbox_tts/` - Configuration and data directory