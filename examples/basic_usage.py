"""
Basic usage examples for Chatterbox TTS.
"""

import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chatterbox_tts.core.processor import tts_processor
from chatterbox_tts.core.voice_manager import voice_manager


async def basic_text_to_speech():
    """Basic text-to-speech example."""
    print("🎤 Basic Text-to-Speech Example")
    
    # Simple text conversion
    text = "Hello! This is a basic text-to-speech example using Chatterbox TTS."
    
    try:
        audio_path = await tts_processor.process_text(text)
        print(f"✓ Audio saved to: {audio_path}")
    except Exception as e:
        print(f"⚠️  Note: Requires TTS backend - {e}")
        print("  Install a TTS backend like Coqui TTS or use mock mode")


async def voice_selection_example():
    """Voice selection example."""
    print("\n🗣️  Voice Selection Example")
    
    voices = voice_manager.list_voices()
    if voices:
        print("Available voices:")
        for voice in voices:
            print(f"  - {voice.id}: {voice.name} ({voice.language})")
    else:
        print("No voices configured. Add voices to config.yaml")


async def file_processing_example():
    """File processing example."""
    print("\n📄 File Processing Example")
    
    # Create a sample text file
    sample_text = """
    This is a sample text file for testing Chatterbox TTS.
    
    It contains multiple paragraphs and sentences to demonstrate
    the document processing capabilities.
    
    Features include:
    - Multi-paragraph support
    - Sentence segmentation
    - Audio stitching
    """
    
    sample_file = Path("sample.txt")
    sample_file.write_text(sample_text)
    
    try:
        audio_path = await tts_processor.process_file(str(sample_file))
        print(f"✓ File processed, audio saved to: {audio_path}")
    except Exception as e:
        print(f"⚠️  Note: Requires TTS backend - {e}")
    
    # Clean up
    if sample_file.exists():
        sample_file.unlink()


async def advanced_settings_example():
    """Advanced settings example."""
    print("\n⚙️  Advanced Settings Example")
    
    text = "This demonstrates advanced TTS settings like speed and pitch control."
    
    try:
        audio_path = await tts_processor.process_text(
            text=text,
            voice_id="default",
            speed=1.5,  # 50% faster
            pitch=0.8,  # Lower pitch
            stitch_audio=True
        )
        print(f"✓ Audio with custom settings saved to: {audio_path}")
    except Exception as e:
        print(f"⚠️  Note: Requires TTS backend - {e}")


async def main():
    """Run all examples."""
    print("🚀 Chatterbox TTS Examples")
    print("=" * 50)
    
    await basic_text_to_speech()
    await voice_selection_example()
    await file_processing_example()
    await advanced_settings_example()
    
    print("\n✨ Examples completed!")
    print("\nNext steps:")
    print("1. Install a TTS backend (Coqui TTS, Microsoft TTS, etc.)")
    print("2. Configure voices in config.yaml")
    print("3. Try the CLI: chatterbox-tts text 'Hello world'")
    print("4. Start the API server: chatterbox-tts serve")


if __name__ == "__main__":
    asyncio.run(main())