#!/usr/bin/env python3
"""
Simplified Chatterbox TTS Installer
Focuses on essential setup without complex modular structure
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path
import shutil
import venv

class SimpleInstaller:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.config_dir = Path.home() / ".chatterbox_tts"
        
    def check_python_version(self):
        """Check if Python version is compatible."""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            sys.exit(1)
        print(f"✅ Python {sys.version.split()[0]} detected")
    
    def detect_gpu(self):
        """Detect GPU availability."""
        try:
            import torch
            if torch.cuda.is_available():
                print("✅ CUDA GPU detected")
                return True
            else:
                print("ℹ️  No CUDA GPU detected, using CPU")
                return False
        except ImportError:
            print("ℹ️  PyTorch not installed yet, will check after setup")
            return None
    
    def create_venv(self):
        """Create virtual environment."""
        if self.venv_path.exists():
            print("ℹ️  Virtual environment already exists")
            return
        
        print("Creating virtual environment...")
        venv.create(self.venv_path, with_pip=True)
        print("✅ Virtual environment created")
    
    def get_pip_path(self):
        """Get pip path for virtual environment."""
        if platform.system() == "Windows":
            return self.venv_path / "Scripts" / "pip.exe"
        return self.venv_path / "bin" / "pip"
    
    def get_python_path(self):
        """Get Python path for virtual environment."""
        if platform.system() == "Windows":
            return self.venv_path / "Scripts" / "python.exe"
        return self.venv_path / "bin" / "python"
    
    def install_dependencies(self, use_gpu=False):
        """Install required packages."""
        pip_path = str(self.get_pip_path())
        
        print("Installing dependencies...")
        
        # Install base requirements
        cmd = [pip_path, "install", "-r", "requirements_simple.txt"]
        subprocess.run(cmd, check=True)
        
        # Install CUDA dependencies if requested
        if use_gpu:
            print("Installing CUDA dependencies...")
            subprocess.run([pip_path, "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"], check=True)
        
        # Install chatterbox-tts in development mode
        print("Installing chatterbox-tts...")
        subprocess.run([pip_path, "install", "-e", "."], check=True)
        
        print("✅ Dependencies installed")
    
    def create_directories(self):
        """Create necessary directories."""
        dirs = [
            self.config_dir,
            self.config_dir / "input",
            self.config_dir / "output",
            self.config_dir / "temp",
            self.config_dir / "logs",
            self.config_dir / "cache" / "models",
            self.config_dir / "cache" / "audio"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("✅ Directories created")
    
    def create_config(self):
        """Create simplified configuration."""
        config = {
            "server": {
                "host": "0.0.0.0",
                "port": 2049,
                "log_level": "INFO"
            },
            "storage": {
                "base_directory": str(self.config_dir)
            },
            "voices": {
                "default": "microsoft_speecht5"
            }
        }
        
        config_file = self.config_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration created")
    
    def create_startup_scripts(self):
        """Create startup scripts."""
        # Create run_server script
        if platform.system() == "Windows":
            server_script = self.project_root / "run_server.bat"
            server_content = f"""@echo off
cd /d "{self.project_root}"
call venv\\Scripts\\activate
python api_listener.py
pause
"""
        else:
            server_script = self.project_root / "run_server.sh"
            server_content = f"""#!/bin/bash
cd "{self.project_root}"
source venv/bin/python
python api_listener.py
"""
        
        with open(server_script, 'w') as f:
            f.write(server_content)
        
        if platform.system() != "Windows":
            os.chmod(server_script, 0o755)
        
        print("✅ Startup scripts created")
    
    def run_setup(self):
        """Run complete setup."""
        print("🚀 Starting Chatterbox TTS Setup")
        print("=" * 40)
        
        try:
            self.check_python_version()
            gpu_available = self.detect_gpu()
            self.create_venv()
            self.install_dependencies(use_gpu=gpu_available or False)
            self.create_directories()
            self.create_config()
            self.create_startup_scripts()
            
            print("\n✅ Setup complete!")
            print(f"\nConfiguration directory: {self.config_dir}")
            print("\nTo start the server:")
            if platform.system() == "Windows":
                print("  run_server.bat")
            else:
                print("  ./run_server.sh")
            print("\nOr manually:")
            print(f"  cd {self.project_root}")
            print("  source venv/bin/activate  # or venv\\Scripts\\activate on Windows")
            print("  python api_listener.py")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Setup failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    installer = SimpleInstaller()
    installer.run_setup()