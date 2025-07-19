# Chatterbox TTS

Advanced Text-to-Speech system with multiple voices, document processing, and REST API.

## Features

- **Multiple Voice Support**: Support for various TTS voices and models
- **Document Processing**: Process text files, markdown, and other formats
- **Audio Stitching**: Seamlessly combine multiple audio segments
- **REST API**: Full-featured API for integration
- **CLI Interface**: Command-line tools for batch processing
- **Voice Management**: Download, manage, and switch between voices
- **Real-time Processing**: Fast processing with async support
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

### Quick Install
```bash
# Clone the repository
git clone https://github.com/chatterbox-tts/chatterbox-tts.git
cd chatterbox-tts

# Run the interactive setup
python interactive_setup.py

# Or use the shell script
chmod +x setup_chatterbox_tts.sh
./setup_chatterbox_tts.sh
```

### Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Development Installation
```bash
# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### CLI Usage

```bash
# Convert text to speech
chatterbox-tts text "Hello, world!"

# Convert file to speech
chatterbox-tts file document.txt

# List available voices
chatterbox-tts voices

# Start the API server
chatterbox-tts serve
```

### API Usage

Start the server:
```bash
chatterbox-tts serve --host 0.0.0.0 --port 2049
```

Convert text to speech:
```bash
curl -X POST http://localhost:2049/tts/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!", "voice_id": "default"}'
```

## Configuration

Configuration is managed through `config.yaml`:

```yaml
# Server settings
server:
  host: "127.0.0.1"
  port: 2049
  reload: false
  log_level: "INFO"

# Processing settings
processing:
  max_segment_length: 1000
  crossfade_duration: 0.5
  output_format: "wav"
  sample_rate: 22050

# Voice settings
voices:
  default_voice: "default"
  voices_dir: "./data/voices"
  cache_dir: "./data/cache"

# Storage settings
storage:
  temp_dir: "./data/temp"
  output_dir: "./data/output"
  max_temp_age: 3600  # 1 hour
```

## CLI Commands

### Text Processing
```bash
# Basic text conversion
chatterbox-tts text "Your text here"

# With custom voice and settings
chatterbox-tts text "Hello world" --voice en-US-AriaNeural --speed 1.2 --pitch 1.1

# Get processing estimate
chatterbox-tts text "Long text..." --estimate
```

### File Processing
```bash
# Process a file
chatterbox-tts file document.txt

# Analyze before processing
chatterbox-tts file document.txt --analyze

# Custom output location
chatterbox-tts file input.txt --output custom.wav
```

### Voice Management
```bash
# List voices
chatterbox-tts voices

# Download a voice
chatterbox-tts download en-US-AriaNeural

# Set default voice
chatterbox-tts voices en-US-AriaNeural set-default

# Remove a voice
chatterbox-tts remove en-US-AriaNeural
```

### Server Management
```bash
# Start server
chatterbox-tts serve

# Custom host/port
chatterbox-tts serve --host 0.0.0.0 --port 8080

# Development mode
chatterbox-tts serve --reload
```

## API Endpoints

### Voices
- `GET /voices` - List all voices
- `GET /voices/{voice_id}` - Get voice details
- `POST /voices/{voice_id}/set-default` - Set default voice

### Text-to-Speech
- `POST /tts/text` - Convert text to speech
- `POST /tts/file` - Convert file to speech
- `POST /tts/estimate` - Get processing estimate

### File Analysis
- `POST /analyze/file` - Analyze document

### System
- `GET /health` - Health check
- `GET /status` - System status
- `DELETE /cleanup` - Clean temporary files

## Supported Formats

### Input Formats
- Plain text (.txt)
- Markdown (.md)
- JSON (.json)
- Text files (.text)

### Output Formats
- WAV (.wav)
- MP3 (.mp3) - with additional dependencies
- OGG (.ogg) - with additional dependencies

## Voice Models

### Pre-installed Voices
- `default` - Basic system voice
- `en-US-AriaNeural` - Microsoft Aria (English US)
- `en-GB-SoniaNeural` - Microsoft Sonia (English UK)
- `en-US-JennyNeural` - Microsoft Jenny (English US)

### Custom Voices
You can add custom voice models by placing them in the `data/voices` directory.

## Advanced Usage

### Batch Processing
```bash
# Process multiple files
for file in *.txt; do
    chatterbox-tts file "$file" --output "audio/${file%.txt}.wav"
done
```

### Integration Example
```python
import asyncio
from chatterbox_tts.core.processor import tts_processor

async def convert_text():
    audio_path = await tts_processor.process_text(
        text="Hello from Python!",
        voice_id="default",
        speed=1.2
    )
    print(f"Audio saved to: {audio_path}")

asyncio.run(convert_text())
```

## Troubleshooting

### Common Issues

**Import errors**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Audio playback issues**
- Ensure audio drivers are installed
- Check system audio settings
- Try different output formats

**Memory issues with large files**
- Increase segment size in config
- Use `--no-stitch` for very large files
- Process files in chunks

### Debug Mode
```bash
# Enable verbose logging
chatterbox-tts --verbose text "Debug message"

# Check system status
chatterbox-tts status
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- GitHub Issues: https://github.com/chatterbox-tts/chatterbox-tts/issues
- Documentation: https://chatterbox-tts.readthedocs.io/
- Discord: https://discord.gg/chatterbox-tts