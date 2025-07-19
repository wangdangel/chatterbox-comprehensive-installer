"""
Main TTS processing engine.
Coordinates voice selection, text processing, and audio generation.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from pathlib import Path

import numpy as np

from .config import config_manager
from .voice_manager import voice_manager
from .document_parser import DocumentParser, DocumentInfo, TextSegment
from .audio_stitcher import AudioStitcher, AudioSegment

logger = logging.getLogger(__name__)


class TTSProcessor:
    """Main TTS processing engine."""
    
    def __init__(self):
        self.config = config_manager
        self.voice_manager = voice_manager
        self.audio_stitcher = AudioStitcher()
        self.document_parser = DocumentParser()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Ensure directories exist
        self.config.ensure_directories()
    
    async def process_text(
        self,
        text: str,
        voice_id: str = "default",
        output_path: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
        stitch_audio: bool = True
    ) -> str:
        """
        Process text to speech.
        
        Args:
            text: Text to convert
            voice_id: Voice to use
            output_path: Output file path (auto-generated if None)
            speed: Speech speed multiplier
            pitch: Pitch multiplier
            stitch_audio: Whether to stitch audio segments
            
        Returns:
            Path to generated audio file
        """
        # Parse document
        document = self.document_parser.parse_text(text)
        
        # Process document
        return await self.process_document(
            document,
            voice_id=voice_id,
            output_path=output_path,
            speed=speed,
            pitch=pitch,
            stitch_audio=stitch_audio
        )
    
    async def process_file(
        self,
        file_path: str,
        voice_id: str = "default",
        output_path: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
        stitch_audio: bool = True
    ) -> str:
        """
        Process file to speech.
        
        Args:
            file_path: Path to input file
            voice_id: Voice to use
            output_path: Output file path (auto-generated if None)
            speed: Speech speed multiplier
            pitch: Pitch multiplier
            stitch_audio: Whether to stitch audio segments
            
        Returns:
            Path to generated audio file
        """
        # Parse document
        document = self.document_parser.parse_file(file_path)
        
        # Process document
        return await self.process_document(
            document,
            voice_id=voice_id,
            output_path=output_path,
            speed=speed,
            pitch=pitch,
            stitch_audio=stitch_audio
        )
    
    async def process_document(
        self,
        document: DocumentInfo,
        voice_id: str = "default",
        output_path: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
        stitch_audio: bool = True
    ) -> str:
        """
        Process document to speech.
        
        Args:
            document: Document to process
            voice_id: Voice to use
            output_path: Output file path (auto-generated if None)
            speed: Speech speed multiplier
            pitch: Pitch multiplier
            stitch_audio: Whether to stitch audio segments
            
        Returns:
            Path to generated audio file
        """
        # Get voice configuration
        voice_config = self.voice_manager.get_voice(voice_id)
        if not voice_config:
            raise ValueError(f"Voice not found: {voice_id}")
        
        # Override voice settings if provided
        if speed is not None:
            voice_config.speed = speed
        if pitch is not None:
            voice_config.pitch = pitch
        
        # Generate output path if not provided
        if not output_path:
            output_path = self._generate_output_path(document.filename)
        
        # Process segments
        if document.total_segments == 1 or not stitch_audio:
            # Single segment or no stitching
            segment = document.segments[0]
            audio_path = await self._process_segment(
                segment,
                voice_config,
                output_path
            )
            return audio_path
        else:
            # Multiple segments with stitching
            return await self._process_segments_stitched(
                document.segments,
                voice_config,
                output_path
            )
    
    async def _process_segment(
        self,
        segment: TextSegment,
        voice_config: Any,
        output_path: str
    ) -> str:
        """Process a single text segment."""
        logger.info(f"Processing segment {segment.index}: {len(segment.text)} chars")
        
        # Use segment-specific settings if available
        speed = segment.speed or voice_config.speed
        pitch = segment.pitch or voice_config.pitch
        voice_id = segment.voice_id or voice_config.name
        
        # Generate audio (placeholder implementation)
        audio_data = await self._generate_tts_audio(
            segment.text,
            voice_config,
            speed,
            pitch
        )
        
        # Save audio
        self._save_audio(audio_data, output_path)
        
        return output_path
    
    async def _process_segments_stitched(
        self,
        segments: List,
        voice_config: Any,
        output_path: str
    ) -> str:
        """Process multiple segments and stitch them together."""
        logger.info(f"Processing {len(segments)} segments with stitching")
        
        # Process each segment
        segment_files = []
        
        for i, segment in enumerate(segments):
            segment_output = f"{output_path}.segment_{i}.wav"
            await self._process_segment(segment, voice_config, segment_output)
            segment_files.append(segment_output)
        
        # Create audio segments for stitching
        audio_segments = []
        for file_path in segment_files:
            audio_segments.append(AudioSegment(file_path=file_path))
        
        # Stitch segments
        stitched_audio, _ = self.audio_stitcher.stitch_segments(
            audio_segments,
            crossfade_duration=self.config.config.processing.crossfade_duration
        )
        
        # Save stitched audio
        self._save_audio(stitched_audio, output_path)
        
        # Clean up segment files
        for file_path in segment_files:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        return output_path
    
    async def _generate_tts_audio(
        self,
        text: str,
        voice_config: Any,
        speed: float,
        pitch: float
    ) -> np.ndarray:
        """
        Generate TTS audio for text.
        
        This is a placeholder implementation that would be replaced
        with actual TTS model integration.
        """
        # In a real implementation, this would:
        # 1. Load the TTS model
        # 2. Generate audio using the model
        # 3. Apply speed and pitch modifications
        
        # For now, create a simple sine wave as placeholder
        import numpy as np
        
        # Estimate duration based on text length
        # Rough estimate: 150 words per minute, 5 chars per word
        estimated_duration = max(1.0, len(text) / (150 * 5 / 60))
        
        # Generate placeholder audio (sine wave)
        t = np.linspace(0, estimated_duration, int(22050 * estimated_duration))
        
        # Create a more interesting placeholder
        frequency = 440  # A4 note
        audio = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Add some modulation
        modulation = np.sin(2 * np.pi * 2 * t) * 0.1
        audio = audio * (1 + modulation)
        
        # Apply fade in/out
        fade_samples = int(0.1 * 22050)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        
        audio[:fade_samples] *= fade_in
        audio[-fade_samples:] *= fade_out
        
        return audio
    
    def _save_audio(self, audio_data: np.ndarray, output_path: str):
        """Save audio data to file."""
        try:
            import soundfile as sf
        except ImportError:
            # Fallback to scipy if soundfile not available
            from scipy.io import wavfile
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            wavfile.write(str(output_path), 22050, audio_data)
            return
            
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        sf.write(str(output_path), audio_data, 22050)
    
    def _generate_output_path(self, filename: str) -> str:
        """Generate output file path."""
        output_dir = Path(self.config.get_path("processing", "output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean filename
        clean_name = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not clean_name:
            clean_name = "output"
        
        timestamp = int(time.time())
        output_filename = f"{clean_name}_{timestamp}.wav"
        
        return str(output_dir / output_filename)
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status."""
        return {
            "active_jobs": 0,  # Would track actual jobs
            "completed_jobs": 0,
            "failed_jobs": 0,
            "queue_size": 0
        }
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported input formats."""
        return [".txt", ".md", ".json", ".text"]
    
    def validate_input(self, text: str) -> tuple[bool, str]:
        """Validate input text."""
        if not text or not text.strip():
            return False, "Empty text provided"
        
        if len(text) > 100000:  # 100k characters limit
            return False, "Text too long (max 100,000 characters)"
        
        return True, "Valid input"
    
    async def get_processing_estimate(self, text: str) -> Dict[str, Any]:
        """Get processing time estimate."""
        char_count = len(text)
        
        # Rough estimates based on character count
        segments = max(1, char_count // 1000)
        processing_time = segments * 2  # 2 seconds per segment
        file_size_mb = (char_count * 0.001)  # Rough estimate
        
        return {
            "character_count": char_count,
            "estimated_segments": segments,
            "estimated_processing_time_seconds": processing_time,
            "estimated_file_size_mb": file_size_mb
        }


# Global processor instance
tts_processor = TTSProcessor()