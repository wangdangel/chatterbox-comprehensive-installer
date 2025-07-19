"""
Voice management system for Chatterbox TTS.
Handles voice selection, configuration, and management.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict

from .config import config_manager, VoiceConfig

logger = logging.getLogger(__name__)


@dataclass
class VoiceInfo:
    """Information about a voice."""
    id: str
    name: str
    description: str
    language: str
    gender: str
    model: str
    vocoder: Optional[str] = None
    speaker_embedding: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    is_default: bool = False
    is_downloaded: bool = False
    file_size: Optional[int] = None
    sample_rate: int = 22050


class VoiceManager:
    """Manages voice configurations and operations."""
    
    def __init__(self):
        self.config = config_manager
        self._ensure_voice_directories()
        self._load_builtin_voices()
    
    def _ensure_voice_directories(self):
        """Ensure voice directories exist."""
        for category in ["default", "custom", "downloaded"]:
            path = Path(self.config.get_path("voices", category))
            path.mkdir(parents=True, exist_ok=True)
    
    def _load_builtin_voices(self):
        """Load built-in voice configurations."""
        builtin_voices = {
            "microsoft_speecht5": VoiceConfig(
                name="Microsoft SpeechT5",
                model="microsoft/speecht5_tts",
                vocoder="microsoft/speecht5_hifigan",
                language="en-US",
                gender="neutral",
                description="High-quality neural TTS model"
            ),
            "coqui_tts": VoiceConfig(
                name="Coqui TTS",
                model="tts_models/en/ljspeech/tacotron2-DDC",
                vocoder="vocoder_models/en/ljspeech/hifigan_v2",
                language="en",
                gender="neutral",
                description="Open-source TTS model"
            ),
            "narrator": VoiceConfig(
                name="Narrator",
                model="microsoft/speecht5_tts",
                vocoder="microsoft/speecht5_hifigan",
                language="en-US",
                gender="male",
                speed=0.9,
                description="Professional narrator voice"
            ),
            "storyteller": VoiceConfig(
                name="Storyteller",
                model="microsoft/speecht5_tts",
                vocoder="microsoft/speecht5_hifigan",
                language="en-US",
                gender="female",
                speed=0.85,
                description="Engaging storytelling voice"
            )
        }
        
        # Add built-in voices if not already present
        for voice_id, voice_config in builtin_voices.items():
            if voice_id not in self.config.config.voices:
                self.config.add_voice(voice_id, voice_config)
    
    def list_voices(self) -> List[VoiceInfo]:
        """List all available voices."""
        voices = []
        default_voice = self.config.config.voices.get("default")
        
        for voice_id, voice_config in self.config.config.voices.items():
            if voice_id == "default":
                continue
                
            voice_path = self._get_voice_path(voice_id)
            is_downloaded = self._is_voice_downloaded(voice_id)
            file_size = self._get_voice_size(voice_id) if is_downloaded else None
            
            voice_info = VoiceInfo(
                id=voice_id,
                name=voice_config.name,
                description=voice_config.description or "",
                language=voice_config.language,
                gender=voice_config.gender,
                model=voice_config.model,
                vocoder=voice_config.vocoder,
                speaker_embedding=voice_config.speaker_embedding,
                speed=voice_config.speed,
                pitch=voice_config.pitch,
                is_default=default_voice == voice_config,
                is_downloaded=is_downloaded,
                file_size=file_size
            )
            voices.append(voice_info)
        
        return sorted(voices, key=lambda v: (not v.is_default, v.name))
    
    def get_voice(self, voice_id: str) -> Optional[VoiceConfig]:
        """Get voice configuration by ID."""
        if voice_id == "default":
            return self.config.config.voices.get("default")
        return self.config.config.voices.get(voice_id)
    
    def set_default_voice(self, voice_id: str) -> bool:
        """Set the default voice."""
        if voice_id in self.config.config.voices:
            self.config.set_default_voice(voice_id)
            logger.info(f"Set default voice to: {voice_id}")
            return True
        return False
    
    def add_custom_voice(self, voice_id: str, config: VoiceConfig) -> bool:
        """Add a custom voice configuration."""
        try:
            self.config.add_voice(voice_id, config)
            logger.info(f"Added custom voice: {voice_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add custom voice {voice_id}: {e}")
            return False
    
    def remove_voice(self, voice_id: str) -> bool:
        """Remove a voice configuration."""
        if voice_id in ["microsoft_speecht5", "coqui_tts", "narrator", "storyteller"]:
            logger.warning(f"Cannot remove built-in voice: {voice_id}")
            return False
        
        if voice_id in self.config.config.voices:
            del self.config.config.voices[voice_id]
            self.config.save_config()
            
            # Remove voice files
            voice_path = self._get_voice_path(voice_id)
            if voice_path.exists():
                shutil.rmtree(voice_path)
            
            logger.info(f"Removed voice: {voice_id}")
            return True
        return False
    
    def download_voice(self, voice_id: str) -> bool:
        """Download voice model files."""
        voice_config = self.get_voice(voice_id)
        if not voice_config:
            logger.error(f"Voice not found: {voice_id}")
            return False
        
        if self._is_voice_downloaded(voice_id):
            logger.info(f"Voice already downloaded: {voice_id}")
            return True
        
        try:
            logger.info(f"Downloading voice: {voice_id}")
            # This would implement actual model downloading
            # For now, we'll create a placeholder
            voice_path = self._get_voice_path(voice_id)
            voice_path.mkdir(parents=True, exist_ok=True)
            
            # Create metadata file
            metadata = {
                "voice_id": voice_id,
                "config": asdict(voice_config),
                "downloaded_at": str(Path().cwd()),
                "version": "1.0"
            }
            
            with open(voice_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Voice downloaded successfully: {voice_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download voice {voice_id}: {e}")
            return False
    
    def _get_voice_path(self, voice_id: str) -> Path:
        """Get the storage path for a voice."""
        # Determine category based on voice type
        if voice_id in ["microsoft_speecht5", "coqui_tts", "narrator", "storyteller"]:
            category = "default"
        else:
            category = "custom"
        
        return Path(self.config.get_path("voices", category)) / voice_id
    
    def _is_voice_downloaded(self, voice_id: str) -> bool:
        """Check if voice model files are downloaded."""
        voice_path = self._get_voice_path(voice_id)
        metadata_file = voice_path / "metadata.json"
        return metadata_file.exists()
    
    def _get_voice_size(self, voice_id: str) -> Optional[int]:
        """Get the size of downloaded voice files in bytes."""
        voice_path = self._get_voice_path(voice_id)
        if not voice_path.exists():
            return None
        
        total_size = 0
        for file_path in voice_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size
    
    def validate_voice_config(self, config: VoiceConfig) -> tuple[bool, str]:
        """Validate voice configuration."""
        if not config.name:
            return False, "Voice name is required"
        
        if not config.model:
            return False, "Model identifier is required"
        
        if config.speed < 0.1 or config.speed > 3.0:
            return False, "Speed must be between 0.1 and 3.0"
        
        if config.pitch < 0.5 or config.pitch > 2.0:
            return False, "Pitch must be between 0.5 and 2.0"
        
        return True, "Valid configuration"
    
    def export_voice_config(self, voice_id: str, output_path: str) -> bool:
        """Export voice configuration to file."""
        voice_config = self.get_voice(voice_id)
        if not voice_config:
            return False
        
        try:
            with open(output_path, "w") as f:
                json.dump(asdict(voice_config), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to export voice config: {e}")
            return False
    
    def import_voice_config(self, config_path: str, voice_id: str) -> bool:
        """Import voice configuration from file."""
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
            
            voice_config = VoiceConfig(**config_data)
            is_valid, message = self.validate_voice_config(voice_config)
            
            if not is_valid:
                logger.error(f"Invalid voice config: {message}")
                return False
            
            self.add_custom_voice(voice_id, voice_config)
            return True
            
        except Exception as e:
            logger.error(f"Failed to import voice config: {e}")
            return False


# Global voice manager instance
voice_manager = VoiceManager()