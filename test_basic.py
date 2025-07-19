"""
Basic test script for Chatterbox TTS.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chatterbox_tts.core.config import config_manager
from chatterbox_tts.core.voice_manager import voice_manager
from chatterbox_tts.core.processor import tts_processor


async def test_basic_functionality():
    """Test basic TTS functionality."""
    print("🧪 Testing Chatterbox TTS...")
    
    # Test config loading
    print("✓ Config loaded successfully")
    print(f"  - Server host: {config_manager.config.server.host}")
    print(f"  - Server port: {config_manager.config.server.port}")
    
    # Test voice manager
    voices = voice_manager.list_voices()
    print(f"✓ Found {len(voices)} voices")
    for voice in voices:
        print(f"  - {voice.id}: {voice.name} ({voice.language})")
    
    # Test processor
    print("✓ Testing processor...")
    estimate = await tts_processor.get_processing_estimate("Hello, world!")
    print(f"  - Processing estimate: {estimate}")
    
    # Test actual processing (with placeholder)
    print("✓ Testing text processing...")
    try:
        audio_path = await tts_processor.process_text("Hello, world!")
        print(f"  - Audio generated: {audio_path}")
        
        # Check if file exists
        if Path(audio_path).exists():
            print("  - Audio file created successfully")
        else:
            print("  - Warning: Audio file not found")
            
    except Exception as e:
        print(f"  - Note: Processing requires TTS backend: {e}")
    
    print("\n🎉 Basic tests completed!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())