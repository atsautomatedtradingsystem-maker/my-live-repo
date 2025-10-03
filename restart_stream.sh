#!/bin/bash
set -e
# Безкінечний цикл: запускає stream_frames.py, якщо впав — перезапускає через 5s
if [ -f "./stream.env" ]; then
  set -o allexport; source ./stream.env; set +o allexport
fi
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

while true; do
  echo "=== START STREAM — $(date) ==="
  python3 stream_frames.py
  rc=$?
  echo "stream_frames.py exited with code $rc at $(date). Restarting in 5s..."
  sleep 5
done
