# render_test.py
from live_stream_adapter import build_stream_figure
import os, sys

try:
    import plotly.io as pio
    from PIL import Image
    import io
except Exception:
    print("Missing plotly/kaleido or PIL — install packages first", file=sys.stderr)
    raise

fig = build_stream_figure(width=640, height=360, t_seconds=1.23)
if fig is None:
    print("ADAPTER: returned None", file=sys.stderr)
    sys.exit(1)

if hasattr(fig, "to_dict") or hasattr(fig, "data"):
    img_bytes = pio.to_image(fig, format="png", width=640, height=360)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
else:
    img = fig.convert("RGB")

img.save("frame_test.png")
print("Saved frame_test.png")
