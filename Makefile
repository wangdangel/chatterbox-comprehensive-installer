.PHONY: install dev test lint format clean build serve

# Default target
all: install

# Install the package
install:
	pip install -e .

# Install development dependencies
dev:
	pip install -e ".[dev]"

# Run tests
test:
	python test_basic.py
	pytest tests/ -v

# Run linting
lint:
	flake8 src/
	mypy src/

# Format code
format:
	black src/
	isort src/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build package
build:
	python setup.py sdist bdist_wheel

# Start development server
serve:
	chatterbox-tts serve --reload --host 0.0.0.0 --port 2049

# Install dependencies
deps:
	pip install -r requirements.txt

# Quick setup
setup:
	chmod +x setup_chatterbox_tts.sh
	./setup_chatterbox_tts.sh

# Help
help:
	@echo "Available targets:"
	@echo "  install  - Install the package"
	@echo "  dev      - Install development dependencies"
	@echo "  test     - Run tests"
	@echo "  lint     - Run linting"
	@echo "  format   - Format code"
	@echo "  clean    - Clean build artifacts"
	@echo "  build    - Build package"
	@echo "  serve    - Start development server"
	@echo "  deps     - Install dependencies"
	@echo "  setup    - Run interactive setup"