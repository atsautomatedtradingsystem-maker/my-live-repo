#!/bin/bash
# Headless stream script for Codespaces (requires Xvfb, chromium, ffmpeg installed)

DISPLAY_NUM=":99"
WIDTH=1280
HEIGHT=720
FRAMERATE=25

STREAM_KEY="${YT_KEY}"
if [ -z "${STREAM_KEY}" ]; then
  echo "ERROR: YT_KEY not set. Add as Codespaces secret or run: export YT_KEY=your_key"
  exit 1
fi

RTMP_URL="rtmp://a.rtmp.youtube.com/live2/${STREAM_KEY}"

# Start virtual X server
Xvfb ${DISPLAY_NUM} -screen 0 ${WIDTH}x${HEIGHT}x24 >/tmp/xvfb.log 2>&1 &

sleep 1

export DISPLAY=${DISPLAY_NUM}
chromium --no-sandbox --disable-gpu --window-size=${WIDTH},${HEIGHT} --app=http://127.0.0.1:8050/ >/tmp/chromium.log 2>&1 &

sleep 2

# Capture X11 display and stream to YouTube; add silent audio source
ffmpeg -f x11grab -r ${FRAMERATE} -s ${WIDTH}x${HEIGHT} -i ${DISPLAY_NUM}.0 \
  -f lavfi -i aevalsrc=0 \
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -g $((FRAMERATE*2)) -b:v 2500k -maxrate 2500k -bufsize 5000k \
  -c:a aac -ar 44100 -b:a 128k -f flv "${RTMP_URL}"
