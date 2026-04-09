#!/bin/bash
# RajeshGPT - Streamlit Quick Start (Linux/Mac)

echo "===================================="
echo "   RajeshGPT - Streamlit Edition"
echo "===================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9+ first"
    exit 1
fi

echo "[1/3] Checking dependencies..."
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "[2/3] Installing requirements..."
    pip3 install -r requirements.txt
else
    echo "[2/3] Dependencies already installed"
fi

echo ""
echo "[3/3] Starting RajeshGPT..."
echo ""
echo "✓ Opening http://localhost:8501"
echo "✓ Press CTRL+C to stop"
echo ""

streamlit run app.py
