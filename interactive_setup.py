#!/usr/bin/env python3
"""
Interactive setup script for Chatterbox TTS system.
Handles environment detection, creation, and package installation.
"""

import os
import sys
import json
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import yaml

class EnvironmentDetector:
    """Detects existing Python environments and provides recommendations."""
    
    def __init__(self):
        self.system = platform.system()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
    def detect_environments(self) -> List[Dict[str, str]]:
        """Scan for existing Python environments."""
        environments = []
        
        # Check for venv environments
        venv_paths = [
            Path.home() / "venvs",
            Path.cwd() / "venv",
            Path.cwd() / ".venv",
        ]
        
        for venv_path in venv_paths:
            if venv_path.exists():
                for env_dir in venv_path.iterdir():
                    if (env_dir / "bin" / "python").exists() or (env_dir / "Scripts" / "python.exe").exists():
                        env_info = self._get_venv_info(env_dir)
                        if env_info:
                            environments.append(env_info)
        
        # Check for conda environments
        conda_info = self._get_conda_info()
        environments.extend(conda_info)
        
        # Check for poetry environments
        poetry_info = self._get_poetry_info()
        environments.extend(poetry_info)
        
        return environments
    
    def _get_venv_info(self, venv_path: Path) -> Optional[Dict[str, str]]:
        """Get information about a venv environment."""
        try:
            if self.system == "Windows":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"
            
            if python_exe.exists():
                result = subprocess.run(
                    [str(python_exe), "--version"],
                    capture_output=True,
                    text=True
                )
                version = result.stdout.strip().split()[1]
                
                return {
                    "type": "venv",
                    "name": venv_path.name,
                    "path": str(venv_path),
                    "version": version,
                    "status": "ready"
                }
        except Exception:
            pass
        return None
    
    def _get_conda_info(self) -> List[Dict[str, str]]:
        """Get information about conda environments."""
        environments = []
        try:
            result = subprocess.run(
                ["conda", "env", "list", "--json"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for env_path in data.get("envs", []):
                    env_name = Path(env_path).name
                    if env_name != "base":
                        environments.append({
                            "type": "conda",
                            "name": env_name,
                            "path": env_path,
                            "version": "3.x",
                            "status": "available"
                        })
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return environments
    
    def _get_poetry_info(self) -> List[Dict[str, str]]:
        """Get information about poetry environments."""
        environments = []
        try:
            # Look for poetry projects
            for pyproject in Path.cwd().rglob("pyproject.toml"):
                project_dir = pyproject.parent
                try:
                    result = subprocess.run(
                        ["poetry", "env", "info", "--path"],
                        cwd=project_dir,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        env_path = result.stdout.strip()
                        environments.append({
                            "type": "poetry",
                            "name": project_dir.name,
                            "path": env_path,
                            "version": "3.x",
                            "status": "available"
                        })
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass
        except Exception:
            pass
        return environments

class InteractiveSetup:
    """Handles interactive environment setup."""
    
    def __init__(self):
        self.detector = EnvironmentDetector()
        self.config = {
            "port": 2049,
            "voice": "microsoft_speecht5",
            "output_dir": "~/chatterbox_tts/output",
            "voices_dir": "~/chatterbox_tts/voices"
        }
    
    def run_setup(self):
        """Run the complete interactive setup."""
        print("\n" + "="*60)
        print("🎙️  Chatterbox TTS Environment Setup")
        print("="*60)
        
        # Check Python version
        if not self._check_python_version():
            return False
        
        # Detect existing environments
        environments = self.detector.detect_environments()
        
        # Show environment selection
        selected_env = self._select_environment(environments)
        if not selected_env:
            return False
        
        # Configure paths and settings
        self._configure_settings()
        
        # Install dependencies
        if not self._install_dependencies(selected_env):
            return False
        
        # Setup complete
        self._setup_complete(selected_env)
        return True
    
    def _check_python_version(self) -> bool:
        """Check if Python 3.8+ is available."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
            print("Please upgrade Python and try again.")
            return False
        
        print(f"✅ Python {version.major}.{version.minor} detected")
        return True
    
    def _select_environment(self, environments: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Interactive environment selection."""
        print("\n📦 Detected Python Environments:")
        print("-" * 40)
        
        if not environments:
            print("No existing environments found.")
            return self._create_new_environment()
        
        # Show existing environments
        for i, env in enumerate(environments, 1):
            marker = " [REC]" if env["type"] == "venv" and "chatterbox" in env["name"].lower() else ""
            status = "✅ Ready" if env["status"] == "ready" else "⚠️  Available"
            print(f"{i}) {env['type']}:{env['name']} (Python {env['version']}){marker}")
            print(f"   Location: {env['path']}")
            print(f"   Status: {status}\n")
        
        print("N) Create New Environment")
        print("D) Use Docker (Advanced)")
        print("Q) Quit")
        
        while True:
            choice = input("\nSelect environment (1-{}, N, D, Q): ".format(len(environments))).strip()
            
            if choice.upper() == 'Q':
                return None
            elif choice.upper() == 'N':
                return self._create_new_environment()
            elif choice.upper() == 'D':
                return self._setup_docker()
            elif choice.isdigit() and 1 <= int(choice) <= len(environments):
                return environments[int(choice) - 1]
            else:
                print("Invalid choice. Please try again.")
    
    def _create_new_environment(self) -> Optional[Dict[str, str]]:
        """Create a new Python environment."""
        print("\n🆕 Create New Environment")
        print("-" * 30)
        print("1) venv - Standard Python virtual environment [REC]")
        print("2) conda - Anaconda/Miniconda environment")
        print("3) poetry - Modern dependency management")
        print("4) pipenv - Traditional virtual environment")
        
        while True:
            choice = input("\nSelect environment type (1-4): ").strip()
            
            if choice == "1":
                return self._create_venv()
            elif choice == "2":
                return self._create_conda_env()
            elif choice == "3":
                return self._create_poetry_env()
            elif choice == "4":
                return self._create_pipenv()
            else:
                print("Invalid choice. Please try again.")
    
    def _create_venv(self) -> Optional[Dict[str, str]]:
        """Create a new venv environment."""
        env_name = input("Environment name [chatterbox_tts]: ").strip() or "chatterbox_tts"
        env_path = Path.home() / "venvs" / env_name
        
        try:
            print(f"Creating venv environment: {env_path}")
            subprocess.run([sys.executable, "-m", "venv", str(env_path)], check=True)
            
            return {
                "type": "venv",
                "name": env_name,
                "path": str(env_path),
                "version": self.detector.python_version,
                "status": "ready"
            }
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create venv: {e}")
            return None
    
    def _create_conda_env(self) -> Optional[Dict[str, str]]:
        """Create a new conda environment."""
        env_name = input("Environment name [chatterbox_tts]: ").strip() or "chatterbox_tts"
        
        try:
            print(f"Creating conda environment: {env_name}")
            subprocess.run(["conda", "create", "-n", env_name, "python=3.9", "-y"], check=True)
            
            conda_prefix = Path.home() / "anaconda3" / "envs" / env_name
            if not conda_prefix.exists():
                conda_prefix = Path.home() / "miniconda3" / "envs" / env_name
            
            return {
                "type": "conda",
                "name": env_name,
                "path": str(conda_prefix),
                "version": "3.9",
                "status": "ready"
            }
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create conda environment: {e}")
            return None
    
    def _create_poetry_env(self) -> Optional[Dict[str, str]]:
        """Create a new poetry environment."""
        project_name = input("Project name [chatterbox_tts]: ").strip() or "chatterbox_tts"
        
        try:
            print(f"Creating poetry project: {project_name}")
            subprocess.run(["poetry", "new", project_name], check=True)
            
            project_path = Path.cwd() / project_name
            return {
                "type": "poetry",
                "name": project_name,
                "path": str(project_path),
                "version": "3.9",
                "status": "ready"
            }
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create poetry project: {e}")
            return None
    
    def _create_pipenv(self) -> Optional[Dict[str, str]]:
        """Create a new pipenv environment."""
        project_name = input("Project name [chatterbox_tts]: ").strip() or "chatterbox_tts"
        
        try:
            print(f"Creating pipenv project: {project_name}")
            project_path = Path.cwd() / project_name
            project_path.mkdir(exist_ok=True)
            
            subprocess.run(["pipenv", "--python", "3.9"], cwd=project_path, check=True)
            
            return {
                "type": "pipenv",
                "name": project_name,
                "path": str(project_path),
                "version": "3.9",
                "status": "ready"
            }
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create pipenv environment: {e}")
            return None
    
    def _setup_docker(self) -> Optional[Dict[str, str]]:
        """Setup Docker environment."""
        print("\n🐳 Docker Setup")
        print("-" * 20)
        print("Docker setup will be handled separately.")
        print("Please run: docker-compose up -d")
        return None
    
    def _configure_settings(self):
        """Configure user settings."""
        print("\n⚙️  Configuration Settings")
        print("-" * 30)
        
        # API port
        port = input(f"API port [{self.config['port']}]: ").strip()
        if port:
            self.config['port'] = int(port)
        
        # Output directory
        output_dir = input(f"Output directory [{self.config['output_dir']}]: ").strip()
        if output_dir:
            self.config['output_dir'] = os.path.expanduser(output_dir)
        
        # Voices directory
        voices_dir = input(f"Voices directory [{self.config['voices_dir']}]: ").strip()
        if voices_dir:
            self.config['voices_dir'] = os.path.expanduser(voices_dir)
        
        # Save configuration
        config_path = Path.home() / ".chatterbox_tts" / "config.yaml"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        
        print(f"✅ Configuration saved to {config_path}")
    
    def _install_dependencies(self, env: Dict[str, str]) -> bool:
        """Install required dependencies."""
        print("\n📦 Installing Dependencies")
        print("-" * 30)
        
        try:
            if env["type"] == "venv":
                pip_path = Path(env["path"]) / ("Scripts" if self.detector.system == "Windows" else "bin") / "pip"
                subprocess.run([str(pip_path), "install", "-e", "."], check=True)
            elif env["type"] == "conda":
                subprocess.run(["conda", "install", "-n", env["name"], "-c", "conda-forge", "chatterbox-tts"], check=True)
            elif env["type"] == "poetry":
                subprocess.run(["poetry", "install"], cwd=env["path"], check=True)
            elif env["type"] == "pipenv":
                subprocess.run(["pipenv", "install", "-e", "."], cwd=env["path"], check=True)
            
            print("✅ Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def _setup_complete(self, env: Dict[str, str]):
        """Display setup completion message."""
        print("\n" + "="*60)
        print("🎉 Setup Complete!")
        print("="*60)
        print(f"Environment: {env['type']}:{env['name']}")
        print(f"Location: {env['path']}")
        print(f"API Port: {self.config['port']}")
        print(f"Output Directory: {self.config['output_dir']}")
        print(f"Voices Directory: {self.config['voices_dir']}")
        print("\nTo start the API server:")
        
        if env["type"] == "venv":
            activate_cmd = "source venv/bin/activate" if self.detector.system != "Windows" else "venv\\Scripts\\activate"
            print(f"  {activate_cmd}")
            print("  chatterbox api --port", self.config['port'])
        elif env["type"] == "conda":
            print(f"  conda activate {env['name']}")
            print("  chatterbox api --port", self.config['port'])
        elif env["type"] == "poetry":
            print(f"  cd {env['path']}")
            print("  poetry run chatterbox api --port", self.config['port'])
        elif env["type"] == "pipenv":
            print(f"  cd {env['path']}")
            print("  pipenv run chatterbox api --port", self.config['port'])
        
        print("\nQuick test:")
        print(f"  curl -X POST http://localhost:{self.config['port']}/api/v1/tts/single \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"text\":\"Hello world\",\"voice_id\":\"microsoft_speecht5\"}'")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Interactive setup for Chatterbox TTS")
    parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode")
    parser.add_argument("--port", type=int, default=2049, help="API port")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--voices-dir", help="Voices directory")
    
    args = parser.parse_args()
    
    if args.non_interactive:
        print("Non-interactive mode not implemented yet")
        return
    
    setup = InteractiveSetup()
    success = setup.run_setup()
    
    if success:
        print("\nSetup completed successfully! 🚀")