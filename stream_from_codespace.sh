#!/usr/bin/env bash
set -euo pipefail
# Headless streaming orchestrator for Codespaces
# 1) ensures venv and deps
# 2) boots live.py (retries installing missing python deps automatically up to N times)
# 3) starts Xvfb + chromium
# 4) runs ffmpeg to stream to YouTube (primary RTMP). Adjust BITRATE/RESOLUTION as needed.

# CONFIG
WORKDIR="$(cd "$(dirname "$0")" && pwd)"
VENV="${WORKDIR}/.venv"
PYTHON="${VENV}/bin/python"
PIP="${VENV}/bin/pip"
LIVELOG="${WORKDIR}/live.log"
DISPLAY_NUM=":99"
WIDTH=1280
HEIGHT=720
FRAMERATE=25
# bitrate suitable for 720p; lower if CPU constrained
VIDEO_BITRATE="2000k"
AUDIO_BITRATE="128k"
# stream endpoints
PRIMARY="rtmp://a.rtmp.youtube.com/live2"
# Backup URL if you want to enable it later; comment/uncomment as needed
BACKUP="rtmp://b.rtmp.youtube.com/live2?backup=1"
# Number of automatic attempts to install missing modules
MAX_INSTALL_ATTEMPTS=10

# check YT_KEY
if [ -z "${YT_KEY:-}" ]; then
  echo "ERROR: YT_KEY is not set. Add as Codespaces secret or run: export YT_KEY=your_key"
  exit 1
fi
STREAM_KEY="${YT_KEY}"

# 1) create venv if missing
if [ ! -x "${PYTHON}" ]; then
  echo "Creating virtualenv..."
  python -m venv "${VENV}"
fi

# activate functions
activate_venv() {
  # shellcheck disable=SC1090
  source "${VENV}/bin/activate"
}

activate_venv

echo "Upgrading pip..."
${PIP} install --upgrade pip setuptools wheel

# 2) install base requirements
echo "Installing base requirements..."
${PIP} install -r "${WORKDIR}/requirements.txt"

# helper: try to run live.py, capture ModuleNotFoundError and attempt pip install
attempts=0
while true; do
  attempts=$((attempts+1))
  echo "Starting live.py (attempt ${attempts})..."
  # run live.py and capture stdout/stderr to live.log
  "${PYTHON}" "${WORKDIR}/live.py" &> "${LIVELOG}" &
  LIVE_PID=$!
  sleep 2

  # wait a bit and check if process still running in background
  if kill -0 "${LIVE_PID}" >/dev/null 2>&1; then
    # process started — but it may exit later; wait briefly and inspect logs for ModuleNotFoundError
    sleep 2
    if grep -q "ModuleNotFoundError" "${LIVELOG}" >/dev/null 2>&1; then
      echo "Found ModuleNotFoundError in ${LIVELOG}. Will try to auto-install."
      kill "${LIVE_PID}" || true
    else
      echo "live.py appears to be running. Proceeding."
      break
    fi
  else
    echo "live.py process exited quickly; checking log for missing module..."
  fi

  # extract missing module name
  missing=$(grep "ModuleNotFoundError" "${LIVELOG}" | tail -n1 | sed -E "s/.*No module named '([^']+)'.*/\1/")
  if [ -z "${missing}" ]; then
    echo "No ModuleNotFoundError found but live.py exited. See ${LIVELOG} for details."
    cat "${LIVELOG}"
    exit 1
  fi
  echo "Detected missing module: ${missing}"

  # map some common module->pip package name differences
  case "${missing}" in
    sklearn) pkg="scikit-learn" ;;
    cv2) pkg="opencv-python" ;;
    yaml) pkg="pyyaml" ;;
    boto3) pkg="boto3" ;;
    faiss) pkg="faiss-cpu" ;;
    faiss_cv) pkg="faiss-cpu" ;;
    _*) pkg="${missing}" ;; # default fallback
    *) pkg="${missing}" ;;
  esac

  echo "Attempting pip install ${pkg} ..."
  ${PIP} install "${pkg}" || {
    echo "pip install ${pkg} failed; try installing build deps or check logs."
    # try common build deps for lightgbm
    if [ "${pkg}" = "lightgbm" ]; then
      echo "Retry: installing system build deps for lightgbm (if sudo available)..."
      sudo apt-get update && sudo apt-get install -y build-essential libomp-dev || true
      ${PIP} install lightgbm || true
    fi
  }

  if [ "${attempts}" -ge "${MAX_INSTALL_ATTEMPTS}" ]; then
    echo "Reached max install attempts (${MAX_INSTALL_ATTEMPTS}). Stop."
    echo "Last ${LIVELOG}:"
    tail -n 200 "${LIVELOG}"
    exit 1
  fi

  echo "Retrying live.py..."
  sleep 1
done

# At this point live.py is running (hopefully)
echo "live.py started successfully. Showing last lines of ${LIVELOG}:"
tail -n 80 "${LIVELOG}"

# 3) start Xvfb and chromium in background
echo "Starting Xvfb on ${DISPLAY_NUM}..."
Xvfb "${DISPLAY_NUM}" -screen 0 ${WIDTH}x${HEIGHT}x24 >/tmp/xvfb.log 2>&1 &
XVFB_PID=$!
sleep 1

export DISPLAY=${DISPLAY_NUM}

echo "Launching chromium in headless app window..."
# --no-sandbox required in many containers
chromium --no-sandbox --disable-gpu --window-size=${WIDTH},${HEIGHT} --app=http://127.0.0.1:8050/ >/tmp/chromium.log 2>&1 &
CHROM_PID=$!
sleep 2

# 4) start ffmpeg to capture X11 display and stream to YouTube
# Using lower resolution and bitrate to reduce CPU load.
# Note: You can customize/raise -b:v if Codespace has enough CPU.
FFMPEG_CMD=(ffmpeg
  -f x11grab -r ${FRAMERATE} -s ${WIDTH}x${HEIGHT} -i ${DISPLAY_NUM}.0
  -f lavfi -i aevalsrc=0
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -g $((FRAMERATE*2)) -b:v ${VIDEO_BITRATE} -maxrate ${VIDEO_BITRATE} -bufsize 2M
  -c:a aac -ar 44100 -b:a ${AUDIO_BITRATE}
  -f flv "${PRIMARY}/${STREAM_KEY}"
)

echo "Starting ffmpeg (streaming to primary)..."
"${FFMPEG_CMD[@]}" 2>&1 | tee /tmp/ffmpeg_stream.log
# If ffmpeg exits, logs are in /tmp/ffmpeg_stream.log
