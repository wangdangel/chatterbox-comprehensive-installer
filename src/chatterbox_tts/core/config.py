"""
Configuration management for Chatterbox TTS.
Handles loading, validation, and management of configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server configuration settings."""
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=2049, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    reload: bool = Field(default=False, description="Enable auto-reload")
    log_level: str = Field(default="INFO", description="Logging level")


class VoiceConfig(BaseModel):
    """Voice configuration for a specific voice."""
    name: str = Field(description="Human-readable voice name")
    model: str = Field(description="Model identifier or path")
    vocoder: Optional[str] = Field(default=None, description="Vocoder model")
    speaker_embedding: Optional[str] = Field(default=None, description="Speaker embedding file")
    language: str = Field(default="en-US", description="Language code")
    gender: str = Field(default="neutral", description="Voice gender")
    speed: float = Field(default=1.0, description="Speech speed multiplier")
    pitch: float = Field(default=1.0, description="Pitch multiplier")
    description: Optional[str] = Field(default=None, description="Voice description")


class ProcessingConfig(BaseModel):
    """Processing configuration settings."""
    chunk_size: int = Field(default=1000, description="Characters per chunk")
    max_chunk_size: int = Field(default=2000, description="Maximum chunk size")
    overlap_size: int = Field(default=50, description="Overlap between chunks")
    stitch_audio: bool = Field(default=True, description="Auto-stitch audio chunks")
    crossfade_duration: float = Field(default=0.5, description="Crossfade duration in seconds")


class AudioConfig(BaseModel):
    """Audio output configuration."""
    sample_rate: int = Field(default=22050, description="Audio sample rate")
    bit_depth: int = Field(default=16, description="Audio bit depth")
    channels: int = Field(default=1, description="Number of audio channels")
    format: str = Field(default="wav", description="Audio format")
    quality: str = Field(default="high", description="Audio quality level")


class StorageConfig(BaseModel):
    """Storage configuration for file paths."""
    base_directory: str = Field(default="~/chatterbox_tts", description="Base storage directory")
    
    class PathsConfig(BaseModel):
        """Nested path configurations."""
        voices: Dict[str, str] = Field(default_factory=lambda: {
            "default": "./voices/default",
            "custom": "./voices/custom",
            "downloaded": "./voices/downloaded"
        })
        processing: Dict[str, str] = Field(default_factory=lambda: {
            "input": "./input",
            "output": "./output",
            "temp": "./temp",
            "logs": "./logs"
        })
        cache: Dict[str, str] = Field(default_factory=lambda: {
            "models": "./cache/models",
            "audio": "./cache/audio"
        })
        backups: Dict[str, str] = Field(default_factory=lambda: {
            "location": "./backups",
            "retention_days": "30"
        })
    
    paths: PathsConfig = Field(default_factory=PathsConfig)


class APIConfig(BaseModel):
    """API configuration settings."""
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:2049"])
    max_file_size: int = Field(default=100, description="Maximum file size in MB")
    request_timeout: int = Field(default=300, description="Request timeout in seconds")
    rate_limit: str = Field(default="100/minute", description="Rate limit string")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file: str = Field(default="./logs/chatterbox.log", description="Log file path")
    max_size: str = Field(default="10MB", description="Maximum log file size")
    backup_count: int = Field(default=5, description="Number of backup log files")


class AdvancedConfig(BaseModel):
    """Advanced configuration options."""
    gpu_enabled: bool = Field(default=True, description="Enable GPU acceleration")
    gpu_memory_fraction: float = Field(default=0.8, description="GPU memory fraction to use")
    preload_models: bool = Field(default=True, description="Preload models on startup")
    cleanup_temp_files: bool = Field(default=True, description="Clean up temporary files")
    enable_metrics: bool = Field(default=False, description="Enable metrics collection")


class Config(BaseModel):
    """Main configuration class."""
    server: ServerConfig = Field(default_factory=ServerConfig)
    voices: Dict[str, VoiceConfig] = Field(default_factory=dict)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self._expand_paths()
    
    def _find_config_file(self) -> str:
        """Find the configuration file."""
        search_paths = [
            "config.yaml",
            "config.yml",
            "~/.chatterbox_tts/config.yaml",
            "~/.chatterbox_tts/config.yml",
            "/etc/chatterbox_tts/config.yaml",
            "/etc/chatterbox_tts/config.yml"
        ]
        
        for path in search_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                return str(expanded_path)
        
        # Return default path
        return "config.yaml"
    
    def _load_config(self) -> Config:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Handle voices configuration
            voices_data = data.pop('voices', {})
            if isinstance(voices_data, dict):
                voices = {}
                for voice_id, voice_config in voices_data.items():
                    if isinstance(voice_config, dict):
                        voices[voice_id] = VoiceConfig(**voice_config)
                    else:
                        voices[voice_id] = voice_config
                data['voices'] = voices
            
            return Config(**data)
            
        except FileNotFoundError:
            # Create default config file
            config = Config()
            self.save_config(config)
            return config
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def _expand_paths(self):
        """Expand all relative paths to absolute paths."""
        base_dir = Path(self.config.storage.base_directory).expanduser()
        
        # Expand storage paths
        for category, paths in self.config.storage.paths.model_dump().items():
            if isinstance(paths, dict):
                for key, path in paths.items():
                    if not Path(path).is_absolute():
                        setattr(
                            getattr(self.config.storage.paths, category),
                            key,
                            str(base_dir / path)
                        )
            else:
                if not Path(paths).is_absolute():
                    setattr(self.config.storage.paths, category, str(base_dir / paths))
    
    def save_config(self, config: Optional[Config] = None):
        """Save configuration to file."""
        config = config or self.config
        config_path = Path(self.config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config.model_dump(exclude_none=True),
                f,
                default_flow_style=False,
                sort_keys=False
            )
    
    def get_voice_config(self, voice_id: str) -> Optional[VoiceConfig]:
        """Get configuration for a specific voice."""
        return self.config.voices.get(voice_id)
    
    def set_default_voice(self, voice_id: str) -> bool:
        """Set the default voice."""
        if voice_id in self.config.voices:
            self.config.voices['default'] = self.config.voices[voice_id]
            self.save_config()
            return True
        return False
    
    def add_voice(self, voice_id: str, config: VoiceConfig):
        """Add a new voice configuration."""
        self.config.voices[voice_id] = config
        self.save_config()
    
    def get_path(self, category: str, key: str) -> str:
        """Get a specific path from storage configuration."""
        paths = getattr(self.config.storage.paths, category, {})
        if isinstance(paths, dict):
            return paths.get(key, "")
        return str(paths)
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.get_path("processing", "input"),
            self.get_path("processing", "output"),
            self.get_path("processing", "temp"),
            self.get_path("processing", "logs"),
            self.get_path("voices", "default"),
            self.get_path("voices", "custom"),
            self.get_path("voices", "downloaded"),
            self.get_path("cache", "models"),
            self.get_path("cache", "audio"),
            self.get_path("backups", "location"),
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


# Global configuration instance
config_manager = ConfigManager()