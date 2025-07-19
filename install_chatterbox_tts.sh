#!/bin/bash

# Chatterbox TTS Dual-Mode Installer
# Provides both simple (basic) and complex (full-featured) installation options
# Works on Linux/macOS with Windows batch equivalent

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}==========================================${NC}"
    echo -e "${PURPLE}  Chatterbox TTS Installation Wizard${NC}"
    echo -e "${PURPLE}==========================================${NC}"
    echo
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to handle errors
handle_error() {
    print_error "An error occurred on line $1"
    print_error "Installation failed. Please check the error messages above."
    exit 1
}

# Set trap for error handling
trap 'handle_error $LINENO' ERR

# Function to check Python availability
check_python() {
    local python_cmd=""
    local python_version=""
    
    # Check for python3 first, then python
    if command_exists python3; then
        python_cmd="python3"
    elif command_exists python; then
        # Check if it's Python 3
        if python --version 2>&1 | grep -q "Python 3"; then
            python_cmd="python"
        fi
    fi
    
    if [[ -z "$python_cmd" ]]; then
        print_error "Python 3 is not installed or not found in PATH"
        return 1
    fi
    
    # Check version
    python_version=$($python_cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if ! $python_cmd -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_error "Python $python_version is installed, but Python 3.8 or higher is required"
        return 1
    fi
    
    echo "$python_cmd"
    return 0
}

# Function to install Python (Linux/macOS)
install_python_linux_macos() {
    local os_type=$1
    
    print_status "Attempting to install Python 3..."
    
    if [[ "$os_type" == "macos" ]]; then
        if command_exists brew; then
            print_status "Installing Python via Homebrew..."
            brew install python@3.11
            return 0
        else
            print_warning "Homebrew not found. Please install Python manually:"
            print_warning "Visit: https://www.python.org/downloads/"
            return 1
        fi
    elif [[ "$os_type" == "linux" ]]; then
        if command_exists apt-get; then
            print_status "Installing Python via apt..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
            return 0
        elif command_exists yum; then
            print_status "Installing Python via yum..."
            sudo yum install -y python3 python3-pip python3-venv
            return 0
        elif command_exists dnf; then
            print_status "Installing Python via dnf..."
            sudo dnf install -y python3 python3-pip python3-venv
            return 0
        else
            print_warning "Package manager not recognized. Please install Python manually:"
            print_warning "Visit: https://www.python.org/downloads/"
            return 1
        fi
    fi
    
    return 1
}

# Function to create virtual environment
create_venv() {
    local python_cmd=$1
    local venv_path=$2
    
    print_step "Creating virtual environment..."
    $python_cmd -m venv "$venv_path"
    
    if [[ $? -ne 0 ]]; then
        print_error "Failed to create virtual environment"
        return 1
    fi
    
    print_success "Virtual environment created at $venv_path"
    return 0
}

# Function to activate virtual environment
activate_venv() {
    local venv_path=$1
    
    if [[ -f "$venv_path/bin/activate" ]]; then
        # Unix-like systems
        source "$venv_path/bin/activate"
    elif [[ -f "$venv_path/Scripts/activate" ]]; then
        # Windows
        source "$venv_path/Scripts/activate"
    else
        print_error "Virtual environment activation script not found"
        return 1
    fi
    
    return 0
}

# Function to install basic dependencies
install_simple_dependencies() {
    print_step "Installing basic dependencies..."
    
    pip install --upgrade pip
    
    # Install from requirements_simple.txt if it exists
    if [[ -f "requirements_simple.txt" ]]; then
        pip install -r requirements_simple.txt
    else
        # Install basic packages
        pip install fastapi uvicorn pydantic python-multipart numpy soundfile scipy librosa
    fi
    
    print_success "Basic dependencies installed"
}

# Function to install full dependencies
install_complex_dependencies() {
    print_step "Installing full dependencies..."
    
    pip install --upgrade pip
    
    # Install PyTorch with CUDA support first
    print_status "Installing PyTorch (attempting CUDA support)..."
    if pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118; then
        print_success "PyTorch with CUDA support installed"
    else
        print_warning "CUDA version failed, installing CPU-only version..."
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
        print_success "PyTorch CPU-only version installed"
    fi
    
    # Install other dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        pip install transformers fastapi uvicorn pydantic python-multipart numpy soundfile librosa pyyaml click rich aiofiles httpx psutil
    fi
    
    print_success "Full dependencies installed"
}

# Function to setup simple installation
setup_simple() {
    print_header
    echo -e "${CYAN}Simple Installation Mode Selected${NC}"
    echo "This will install:"
    echo "- Basic FastAPI server"
    echo "- Essential audio processing"
    echo "- Simple TTS functionality"
    echo
    
    # Check Python
    local python_cmd=$(check_python)
    if [[ $? -ne 0 ]]; then
        print_error "Python 3.8+ is required for installation"
        read -p "Attempt to install Python automatically? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local os_type=$(detect_os)
            if [[ "$os_type" == "windows" ]]; then
                print_error "Automatic Python installation not supported on Windows"
                print_error "Please install Python 3.8+ from https://www.python.org/downloads/"
                exit 1
            fi
            install_python_linux_macos "$os_type"
            python_cmd=$(check_python)
            if [[ $? -ne 0 ]]; then
                exit 1
            fi
        else
            exit 1
        fi
    fi
    
    # Create project directory
    local project_dir="chatterbox_tts_simple"
    print_step "Creating project directory: $project_dir"
    
    if [[ -d "$project_dir" ]]; then
        print_warning "Directory $project_dir already exists"
        read -p "Remove existing directory? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$project_dir"
        else
            print_error "Installation cancelled"
            exit 1
        fi
    fi
    
    mkdir -p "$project_dir"
    cd "$project_dir"
    
    # Create virtual environment
    create_venv "$python_cmd" "venv"
    activate_venv "venv"
    
    # Install dependencies
    install_simple_dependencies
    
    # Create basic structure
    mkdir -p {input,output,logs}
    
    # Create simple API server
    cat > simple_server.py << 'EOF'
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import shutil
from pathlib import Path

app = FastAPI(title="Chatterbox TTS Simple", version="1.0.0")

# Directories
INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Chatterbox TTS Simple API is running"}

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files supported")
    
    job_id = str(uuid.uuid4())
    input_path = INPUT_DIR / f"{job_id}.txt"
    output_path = OUTPUT_DIR / f"{job_id}.wav"
    
    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Simple TTS placeholder (in real implementation, use actual TTS)
    with open(input_path, 'r') as f:
        text = f.read()
    
    # Create a simple audio file (placeholder - replace with actual TTS)
    import numpy as np
    import soundfile as sf
    
    # Generate simple tone as placeholder
    sample_rate = 22050
    duration = len(text) * 0.1  # 0.1 second per character
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t) * 0.3
    
    sf.write(output_path, audio, sample_rate)
    
    return {"job_id": job_id, "status": "completed", "download_url": f"/download/{job_id}"}

@app.get("/download/{job_id}")
async def download_file(job_id: str):
    output_path = OUTPUT_DIR / f"{job_id}.wav"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(output_path, filename=f"{job_id}.wav")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2049)
EOF
    
    # Create run script
    cat > run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python simple_server.py
EOF
    
    chmod +x run.sh
    
    # Create Windows batch file
    cat > run.bat << 'EOF'
@echo off
call venv\Scripts\activate
python simple_server.py
pause
EOF
    
    print_success "Simple installation completed!"
    echo
    echo -e "${GREEN}To start the server:${NC}"
    echo "  cd $project_dir"
    echo "  ./run.sh    # Linux/macOS"
    echo "  run.bat     # Windows"
    echo
    echo -e "${GREEN}API will be available at:${NC} http://localhost:2049"
}

# Function to setup complex installation
setup_complex() {
    print_header
    echo -e "${CYAN}Complex Installation Mode Selected${NC}"
    echo "This will install:"
    echo "- Full chatterbox-tts package"
    echo "- Advanced TTS models (PyTorch + Transformers)"
    echo "- Complete modular system"
    echo "- Background job processing"
    echo
    
    # Check Python
    local python_cmd=$(check_python)
    if [[ $? -ne 0 ]]; then
        print_error "Python 3.8+ is required for installation"
        read -p "Attempt to install Python automatically? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local os_type=$(detect_os)
            if [[ "$os_type" == "windows" ]]; then
                print_error "Automatic Python installation not supported on Windows"
                print_error "Please install Python 3.8+ from https://www.python.org/downloads/"
                exit 1
            fi
            install_python_linux_macos "$os_type"
            python_cmd=$(check_python)
            if [[ $? -ne 0 ]]; then
                exit 1
            fi
        else
            exit 1
        fi
    fi
    
    # Check if we're in the chatterbox_api directory
    if [[ ! -f "setup.py" ]] && [[ ! -f "pyproject.toml" ]]; then
        print_error "This script should be run from the chatterbox_api directory"
        print_error "Please ensure setup.py or pyproject.toml is present"
        exit 1
    fi
    
    # Create virtual environment
    create_venv "$python_cmd" "venv"
    activate_venv "venv"
    
    # Install complex dependencies
    install_complex_dependencies
    
    # Install the package in development mode
    print_step "Installing chatterbox-tts package..."
    pip install -e .
    
    # Create job directories
    mkdir -p _jobs_input_dir _jobs_output_dir
    
    # Create configuration
    if [[ ! -f "config.yaml" ]]; then
        cat > config.yaml << 'EOF'
# Chatterbox TTS Configuration
app:
  name: "Chatterbox TTS"
  version: "1.0.0"
  debug: false

server:
  host: "0.0.0.0"
  port: 2049
  workers: 1

audio:
  sample_rate: 22050
  format: "wav"
  channels: 1

model:
  name: "microsoft/speecht5_tts"
  device: "auto"  # auto, cpu, cuda
  cache_dir: "./models"

paths:
  input_dir: "_jobs_input_dir"
  output_dir: "_jobs_output_dir"
  log_dir: "logs"
EOF
    fi
    
    # Create run scripts
    cat > run_server.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python -m chatterbox_tts.api.server
EOF
    
    cat > run_cli.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python -m chatterbox_tts.cli.main "$@"
EOF
    
    chmod +x run_server.sh run_cli.sh
    
    # Create Windows batch files
    cat > run_server.bat << 'EOF'
@echo off
call venv\Scripts\activate
python -m chatterbox_tts.api.server
pause
EOF
    
    cat > run_cli.bat << 'EOF'
@echo off
call venv\Scripts\activate
python -m chatterbox_tts.cli.main %*
pause
EOF
    
    print_success "Complex installation completed!"
    echo
    echo -e "${GREEN}Available commands:${NC}"
    echo "  ./run_server.sh    # Start API server"
    echo "  ./run_cli.sh       # CLI interface"
    echo
    echo -e "${GREEN}API will be available at:${NC} http://localhost:2049"
    echo -e "${GREEN}CLI usage:${NC} ./run_cli --help"
}

# Main menu
main_menu() {
    print_header
    
    echo "Please select installation mode:"
    echo
    echo -e "${GREEN}1) Simple Installation${NC}"
    echo "   - Basic FastAPI server"
    echo "   - Essential audio processing"
    echo "   - Lightweight setup"
    echo
    echo -e "${CYAN}2) Complex Installation${NC}"
    echo "   - Full chatterbox-tts package"
    echo "   - Advanced TTS models"
    echo "   - Complete modular system"
    echo
    echo -e "${YELLOW}3) Exit${NC}"
    echo
    
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            setup_simple
            ;;
        2)
            setup_complex
            ;;
        3)
            print_status "Installation cancelled"
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please enter 1, 2, or 3"
            main_menu
            ;;
    esac
}

# Check if running on Windows
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    print_warning "Windows detected. Consider using install_chatterbox_tts.bat instead"
    print_warning "Continuing with bash script..."
fi

# Make the script executable
chmod +x "$0" 2>/dev/null || true

# Start the installation
main_menu