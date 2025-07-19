#!/bin/bash

echo "Setting up GitHub connection for ChatterBox TTS..."
echo

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed or not in PATH"
    echo "Please install Git from https://git-scm.com/"
    exit 1
fi

# Check current status
echo "Current git status:"
git status
echo

# Check remote
echo "Current remote configuration:"
git remote -v
echo

echo "To complete the setup:"
echo "1. Create the repository on GitHub: https://github.com/new"
echo "2. Repository name: chatterbox-comprehensive-installer"
echo "3. Don't initialize with README (we already have one)"
echo "4. Run: git push -u origin main"
echo

read -p "Press Enter to continue..."