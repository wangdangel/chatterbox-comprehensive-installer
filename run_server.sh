#!/bin/bash
# Linux/Mac startup script for Chatterbox TTS

echo "Starting Chatterbox TTS Server..."
echo

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "Virtual environment not found. Run 'python simple_install.py' first."
    exit 1
fi

# Check if api_listener.py exists
if [ ! -f "api_listener.py" ]; then
    echo "api_listener.py not found. Please check your installation."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start the server
python api_listener.py