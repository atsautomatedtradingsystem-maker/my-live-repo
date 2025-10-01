# Streamer (Dash -> Chromium -> ffmpeg -> YouTube)

1. Copy `.env.example` -> `.env` and put your `YT_STREAM_KEY` there.
2. Build & run:
   - `docker compose up --build -d`
3. Check logs:
   - `docker compose logs -f streamer`
4. If running on VPS use systemd unit (example provided in README).
