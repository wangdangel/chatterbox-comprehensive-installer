#!/usr/bin/env python3
"""
Test script to verify Chatterbox TTS setup
"""

import os
import sys
import json
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from chatterbox_tts.core.processor import TTSProcessor
        print("✅ TTSProcessor imported successfully")
        
        from chatterbox_tts.core.config import config_manager
        print("✅ config_manager imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_directories():
    """Test if required directories exist."""
    print("\nTesting directories...")
    
    config_dir = Path.home() / ".chatterbox_tts"
    required_dirs = [
        config_dir,
        config_dir / "input",
        config_dir / "output",
        config_dir / "temp",
        config_dir / "logs"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - missing")
            all_exist = False
    
    return all_exist

def test_config():
    """Test configuration file."""
    print("\nTesting configuration...")
    
    config_file = Path.home() / ".chatterbox_tts" / "config.json"
    if not config_file.exists():
        print("❌ config.json not found")
        return False
    
    try:
        with open(config_file) as f:
            config = json.load(f)
        print("✅ config.json loaded successfully")
        print(f"   Server: {config.get('server', {}).get('host', '0.0.0.0')}:{config.get('server', {}).get('port', 2049)}")
        return True
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

def test_processor():
    """Test TTS processor initialization."""
    print("\nTesting TTS processor...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from chatterbox_tts.core.processor import TTSProcessor
        
        processor = TTSProcessor()
        print("✅ TTSProcessor initialized successfully")
        
        # Test validation
        is_valid, message = processor.validate_input("Hello world")
        if is_valid:
            print("✅ Input validation working")
        else:
            print(f"❌ Input validation failed: {message}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Processor test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Chatterbox TTS Setup Test")
    print("=" * 30)
    
    tests = [
        ("Imports", test_imports),
        ("Directories", test_directories),
        ("Configuration", test_config),
        ("Processor", test_processor)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 30)
    print("Test Results:")
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Setup is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()