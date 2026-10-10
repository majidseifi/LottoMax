#!/bin/bash
# Launcher script for Multi-Lottery System GUI

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to that directory
cd "$DIR"

# Launch the GUI application using the venv Python
"$DIR/.venv/bin/python" lotto_gui.py
