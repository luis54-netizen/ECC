#!/usr/bin/env bash
# Crea jarvis-lambda.zip pronto da caricare su AWS Lambda (runtime Python 3.12+).
set -euo pipefail
cd "$(dirname "$0")"
rm -rf build jarvis-lambda.zip
pip install -q -r requirements.txt -t build --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12
cp -r lambda_function.py jarvis build/
(cd build && zip -qr ../jarvis-lambda.zip . -x '*__pycache__*')
rm -rf build
echo "Creato jarvis-lambda.zip"
