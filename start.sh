#!/bin/bash
set -e
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
python app.py