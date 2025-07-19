#!/usr/bin/env python3
"""
Example usage of Chatterbox TTS
Demonstrates both API and direct usage
"""

import asyncio
import requests
import json
from pathlib import Path

def test_api():
    """Test the API endpoints."""
    base_url = "http://localhost:2049"
    
    print("Testing API endpoints...")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        return False
    
    # Test text-to-speech
    try:
        payload = {
            "text": "Hello, this is a test of the Chatterbox TTS system.",
            "voice_id": "microsoft_speecht5",
            "speed": 1.0,
            "pitch": 1.0
        }
        response = requests.post(f"{base_url}/tts", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ TTS API working: {result['filename']}")
            print(f"   Duration: {result['duration']:.2f}s")
            print(f"   Size: {result['file_size']} bytes")
        else:
            print(f"❌ TTS API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ TTS API error: {e}")
        return False
    
    # Test voices endpoint
    try:
        response = requests.get(f"{base_url}/voices")
        if response.status_code == 200:
            voices = response.json()
            print(f"✅ Voices API working: {len(voices)} voices available")
            for voice in voices:
                print(f"   - {voice['id']}: {voice['name']}")
        else:
            print(f"❌ Voices API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Voices API error: {e}")
    
    return True

def test_direct_usage():
    """Test direct usage of the TTS processor."""
    print("\nTesting direct usage...")
    
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from chatterbox_tts.core.processor import TTSProcessor
        
        processor = TTSProcessor()
        
        # Test validation
        is_valid, message = processor.validate_input("Hello world")
        if is_valid:
            print("✅ Input validation working")
        else:
            print(f"❌ Input validation failed: {message}")
            return False
        
        # Test processing estimate
        estimate = asyncio.run(processor.get_processing_estimate("Hello world"))
        print(f"✅ Processing estimate: {estimate['estimated_processing_time_seconds']}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct usage failed: {e}")
        return False

def create_sample_text():
    """Create a sample text file for testing."""
    sample_text = """Welcome to Chatterbox TTS!
    
This is a demonstration of text-to-speech capabilities.
You can convert any text to natural-sounding speech.

Features include:
- Multiple voice options
- Speed and pitch control
- File processing
- API access
- Command-line usage

Try it out with different texts and settings!"""
    
    sample_file = Path("sample_input.txt")
    with open(sample_file, 'w') as f:
        f.write(sample_text)
    
    print(f"✅ Sample file created: {sample_file}")
    return str(sample_file)

def main():
    """Run all tests."""
    print("Chatterbox TTS Example Usage")
    print("=" * 40)
    
    # Create sample file
    sample_file = create_sample_text()
    
    # Test direct usage
    direct_ok = test_direct_usage()
    
    # Test API (if server is running)
    print("\nTo test the API, start the server with:")
    print("  python api_listener.py")
    print("Then run this script again.")
    
    print("\n" + "=" * 40)
    print("Usage examples:")
    print("1. API usage:")
    print("   curl -X POST http://localhost:2049/tts \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"text\": \"Hello world\", \"voice_id\": \"microsoft_speecht5\"}'")
    print()
    print("2. Command line:")
    print("   python tts_processor.py --text 'Hello world' --output hello.wav")
    print()
    print("3. File processing:")
    print(f"   python tts_processor.py --file {sample_file} --output sample.wav")

if __name__ == "__main__":
    main()