#!/usr/bin/env bash
# Exposure Calculator — Auto-install Python if missing, then run

cd "$(dirname "$0")"

# ========== Auto-update from GitHub ==========
if command -v git &>/dev/null && [ -d ".git" ]; then
    git fetch origin main &>/dev/null || true
    git reset --hard origin/main &>/dev/null || true
fi

# ========== Check Python ==========
if command -v python3 &>/dev/null; then
    :
elif command -v python &>/dev/null; then
    alias python3=python
else
    echo ""
    echo "[Exposure Calculator] Python not found. Attempting automatic installation..."
    echo ""

    # Detect OS and install Python
    if command -v apt-get &>/dev/null; then
        echo "[Exposure Calculator] Installing Python via apt (Debian/Ubuntu)..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-tk python3-pip
    elif command -v dnf &>/dev/null; then
        echo "[Exposure Calculator] Installing Python via dnf (Fedora/RHEL)..."
        sudo dnf install -y python3 python3-tkinter
    elif command -v brew &>/dev/null; then
        echo "[Exposure Calculator] Installing Python via Homebrew (macOS)..."
        brew install python-tk@3.12
    elif command -v pacman &>/dev/null; then
        echo "[Exposure Calculator] Installing Python via pacman (Arch)..."
        sudo pacman -S --noconfirm python python-tk
    else
        echo "[Exposure Calculator] Could not detect package manager."
        echo "Please install Python 3 with tkinter manually:"
        echo "  - Debian/Ubuntu: sudo apt install python3 python3-tk"
        echo "  - Fedora:       sudo dnf install python3 python3-tkinter"
        echo "  - macOS:        brew install python-tk"
        echo "  - Or download:  https://www.python.org/downloads/"
        exit 1
    fi

    if ! command -v python3 &>/dev/null; then
        echo "[Exposure Calculator] Installation may have failed. Please run again or install manually."
        exit 1
    fi
    echo "[Exposure Calculator] Python installed. Launching application..."
fi

# ========== Run the application ==========
exec python3 ExposureCalculator.py
