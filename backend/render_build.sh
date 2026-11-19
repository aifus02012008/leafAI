#!/usr/bin/env bash
set -e
pip install --upgrade pip
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu
pip install opencv-python-headless
pip install -r requirements.txt
