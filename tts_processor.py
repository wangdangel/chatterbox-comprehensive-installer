#!/usr/bin/env python3
"""
TTS Worker Script
Standalone script for processing TTS requests from command line or queue
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chatterbox_tts.core.processor import TTSProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TTSWorker:
    """Simple TTS worker for processing requests."""
    
    def __init__(self):
        self.processor = TTSProcessor()
    
    async def process_text(self, text: str, voice_id: str = "microsoft_speecht5", 
                          output_path: Optional[str] = None, **kwargs) -> str:
        """Process text to speech."""
        logger.info(f"Processing text with voice: {voice_id}")
        
        audio_path = await self.processor.process_text(
            text=text,
            voice_id=voice_id,
            output_path=output_path,
            **kwargs
        )
        
        logger.info(f"Audio generated: {audio_path}")
        return audio_path
    
    async def process_file(self, file_path: str, voice_id: str = "microsoft_speecht5",
                          output_path: Optional[str] = None, **kwargs) -> str:
        """Process file to speech."""
        logger.info(f"Processing file: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        audio_path = await self.processor.process_file(
            file_path=file_path,
            voice_id=voice_id,
            output_path=output_path,
            **kwargs
        )
        
        logger.info(f"Audio generated: {audio_path}")
        return audio_path
    
    def get_processing_estimate(self, text: str) -> Dict[str, Any]:
        """Get processing time estimate."""
        return asyncio.run(self.processor.get_processing_estimate(text))
    
    def list_voices(self):
        """List available voices."""
        try:
            from chatterbox_tts.core.voice_manager import voice_manager
            voices = voice_manager.list_voices()
            return [{"id": v.id, "name": v.name, "description": v.description} for v in voices]
        except Exception as e:
            logger.warning(f"Could not load voices: {e}")
            return [{"id": "microsoft_speecht5", "name": "Microsoft SpeechT5", "description": "Default voice"}]

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Chatterbox TTS Worker")
    parser.add_argument("--text", "-t", help="Text to convert to speech")
    parser.add_argument("--file", "-f", help="File to convert to speech")
    parser.add_argument("--voice", "-v", default="microsoft_speecht5", help="Voice ID to use")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed (0.1-3.0)")
    parser.add_argument("--pitch", type=float, default=1.0, help="Pitch multiplier (0.5-2.0)")
    parser.add_argument("--estimate", action="store_true", help="Get processing estimate")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    
    args = parser.parse_args()
    
    worker = TTSWorker()
    
    if args.list_voices:
        voices = worker.list_voices()
        print("Available voices:")
        for voice in voices:
            print(f"  {voice['id']}: {voice['name']} - {voice['description']}")
        return
    
    if args.estimate:
        if not args.text:
            print("Error: --text required for estimate")
            sys.exit(1)
        
        estimate = worker.get_processing_estimate(args.text)
        print(f"Processing estimate for {estimate['character_count']} characters:")
        print(f"  Segments: {estimate['estimated_segments']}")
        print(f"  Time: {estimate['estimated_processing_time_seconds']}s")
        print(f"  File size: {estimate['estimated_file_size_mb']}MB")
        return
    
    if args.text:
        # Process text
        asyncio.run(worker.process_text(
            text=args.text,
            voice_id=args.voice,
            output_path=args.output,
            speed=args.speed,
            pitch=args.pitch
        ))
        
    elif args.file:
        # Process file
        asyncio.run(worker.process_file(
            file_path=args.file,
            voice_id=args.voice,
            output_path=args.output,
            speed=args.speed,
            pitch=args.pitch
        ))
        
    else:
        print("Error: Either --text or --file required")
        sys.exit(1)

if __name__ == "__main__":
    main()