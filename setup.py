"""
Setup script for Chatterbox TTS.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text().splitlines()

setup(
    name="chatterbox-tts",
    version="1.0.0",
    description="Advanced Text-to-Speech system with multiple voices and features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Chatterbox TTS Team",
    author_email="team@chatterbox-tts.com",
    url="https://github.com/chatterbox-tts/chatterbox-tts",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "chatterbox-tts=chatterbox_tts.cli.main:cli",
            "chatterbox-tts-server=chatterbox_tts.api.server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="tts text-to-speech audio voice synthesis",
    project_urls={
        "Bug Reports": "https://github.com/chatterbox-tts/chatterbox-tts/issues",
        "Source": "https://github.com/chatterbox-tts/chatterbox-tts",
        "Documentation": "https://chatterbox-tts.readthedocs.io/",
    },
)