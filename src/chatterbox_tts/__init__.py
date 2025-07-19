"""
Chatterbox TTS - Modular Text-to-Speech System
=============================================

A modern, modular TTS system with enhanced voice management,
document processing, and audio stitching capabilities.
"""

__version__ = "2.0.0"
__author__ = "Chatterbox Team"
__email__ = "team@chatterbox.dev"

from .core.processor import TTSProcessor
from .core.voice_manager import VoiceManager
from .core.audio_stitcher import AudioStitcher
from .core.document_parser import DocumentParser

__all__ = [
    "TTSProcessor",
    "VoiceManager", 
    "AudioStitcher",
    "DocumentParser",
]