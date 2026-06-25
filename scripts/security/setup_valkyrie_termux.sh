#!/usr/bin/env bash
# Termux setup script for Project Valkyrie — run on Android with Termux:API installed

# 1. Install Dependencies
pkg update -y && pkg install python termux-api jq -y
pip install colorama

# 2. Deploy the Valkyrie Engine
DEST="$HOME/SYSTEMS_MASTER_HUB/04_Security_Division/Active_Defense"
mkdir -p "$DEST"
cp "$(dirname "$0")/project_valkyrie.py" "$DEST/"

# 3. Launch
python "$DEST/project_valkyrie.py"
