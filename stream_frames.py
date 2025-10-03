# замініть існуючу render_frame на наступну
def render_frame(t_seconds, width=WIDTH, height=HEIGHT):
    # спробуємо адаптер живого коду
    try:
        from live_stream_adapter import build_stream_figure
        fig = build_stream_figure(width=width, height=height)
        if fig is not None:
            # якщо це plotly-fig
            try:
                import plotly.io as pio, io
                from PIL import Image
                img_bytes = pio.to_image(fig, format="png", width=width, height=height)
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((width, height))
                print(f"ADAPTER: produced image at t={t_seconds:.1f}s", file=sys.stderr)
                return np.array(img, dtype=np.uint8)
            except Exception:
                # якщо вже отримали PIL.Image
                try:
                    if isinstance(fig, Image.Image):
                        img = fig.convert("RGB").resize((width, height))
                        print("ADAPTER: returned PIL image", file=sys.stderr)
                        return np.array(img, dtype=np.uint8)
                except Exception:
                    pass
        # якщо адаптер повернув None — провалуємося в fallback нижче
    except Exception as e:
        print("ADAPTER: import/build failed:", e, file=sys.stderr)

    # ----- fallback simple render -----
    img = Image.new("RGB", (width, height), (18, 18, 28))
    draw = ImageDraw.Draw(img)
    txt = f"time: {t_seconds:.1f}s"
    draw.text((10, 8), txt, fill=(240,240,240))
    cx = int(width/2 + (width/4) * np.sin(t_seconds))
    cy = height//2
    r = 40
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(200,80,80), width=4)
    return np.array(img, dtype=np.uint8)
