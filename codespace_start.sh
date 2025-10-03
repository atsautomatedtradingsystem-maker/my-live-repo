#!/bin/bash
set -e
if [ -f "./stream.env" ]; then
  export $(grep -v '^#' ./stream.env | xargs)
fi
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi
if [ -z "${YT_KEY}" ]; then
  echo "YT_KEY not set. Create stream.env or export YT_KEY in session." >&2
  exit 1
fi
echo "Starting stream_frames.py..."
python3 stream_frames.py
