#!/usr/bin/env python3
# stream_frames.py
import os, sys, time, subprocess, numpy as np
from PIL import Image, ImageDraw

WIDTH = int(os.environ.get("STREAM_WIDTH", 640))
HEIGHT = int(os.environ.get("STREAM_HEIGHT", 360))
FPS = int(os.environ.get("STREAM_FPS", 15))
BITRATE = os.environ.get("STREAM_BITRATE", "1200k")

YT_KEY = os.environ.get("YT_KEY")
YT_PRIMARY = os.environ.get("YT_PRIMARY", "rtmp://a.rtmp.youtube.com/live2")
YT_BACKUP = os.environ.get("YT_BACKUP", "rtmp://b.rtmp.youtube.com/live2")  # no ?backup=1 here

if not YT_KEY:
    print("ERROR: YT_KEY not set", file=sys.stderr)
    sys.exit(1)

ffmpeg_cmd = [
    "ffmpeg",
    "-hide_banner", "-loglevel", "info",
    "-f", "rawvideo",
    "-pix_fmt", "rgb24",
    "-s", f"{WIDTH}x{HEIGHT}",
    "-r", str(FPS),
    "-i", "-",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-b:v", BITRATE,
    "-pix_fmt", "yuv420p",
    "-g", str(FPS*2),
    "-c:a", "aac",
    "-b:a", "128k",
    "-ar", "44100",
    "-f", "flv", f"{YT_PRIMARY}/{YT_KEY}",
    "-f", "flv", f"{YT_BACKUP}/{YT_KEY}?backup=1"
]

print("Starting ffmpeg:", " ".join(ffmpeg_cmd), file=sys.stderr)
proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

def render_frame(t_seconds, width=WIDTH, height=HEIGHT):
    # try adapter -> plotly/kaleido -> PNG; fallback to PIL simple render
    try:
        import io
        import plotly.io as pio
        from PIL import Image
        from live_stream_adapter import build_stream_figure

        fig = build_stream_figure(width=width, height=height)
        if fig is None:
            raise RuntimeError("adapter returned None")
        if hasattr(fig, "to_dict"):
            img_bytes = pio.to_image(fig, format="png", width=width, height=height)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((width, height))
            return np.array(img, dtype=np.uint8)
        if isinstance(fig, Image.Image):
            img = fig.convert("RGB").resize((width, height))
            return np.array(img, dtype=np.uint8)
        raise RuntimeError("unsupported adapter return type")
    except Exception:
        img = Image.new("RGB", (width, height), (18, 18, 28))
        draw = ImageDraw.Draw(img)
        txt = f"time: {t_seconds:.1f}s"
        draw.text((10, 8), txt, fill=(240,240,240))
        cx = int(width/2 + (width/4) * np.sin(t_seconds))
        cy = height//2
        r = 40
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(200,80,80), width=4)
        return np.array(img, dtype=np.uint8)

try:
    t0 = time.time()
    frame_interval = 1.0 / FPS
    while True:
        t = time.time() - t0
        frame = render_frame(t, WIDTH, HEIGHT)
        if frame.shape != (HEIGHT, WIDTH, 3):
            print("ERROR: unexpected frame shape:", frame.shape, file=sys.stderr)
            break
        proc.stdin.write(frame.tobytes())
        proc.stdin.flush()
        time.sleep(frame_interval)
except KeyboardInterrupt:
    print("KeyboardInterrupt — terminating ffmpeg", file=sys.stderr)
finally:
    try:
        proc.stdin.close()
    except Exception:
        pass
    proc.wait()
    print("ffmpeg exited with code", proc.returncode, file=sys.stderr)
