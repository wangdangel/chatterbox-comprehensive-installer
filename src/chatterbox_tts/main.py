"""
Main entry point for Chatterbox TTS.
"""

import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatterbox_tts.cli.main import cli

if __name__ == "__main__":
    cli()