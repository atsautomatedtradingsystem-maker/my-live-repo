def render_frame(t_seconds, width=WIDTH, height=HEIGHT):
    """
    Diagnostic render:
    - намагається отримати фігуру з live_stream_adapter.build_stream_figure(...)
      передаючи t_seconds для динаміки
    - логгирує тип поверненого об'єкту
    - конвертує в PIL->numpy і рахує md5 + стандартне відхилення пікселів
    - зберігає кожний N-й кадр як frame_debug_{i}.png для візуалки
    """
    try:
        import io, sys, hashlib
        import plotly.io as pio
        from PIL import Image, ImageStat
        from live_stream_adapter import build_stream_figure

        # Передаємо t_seconds (дуже важливо для динаміки)
        fig = build_stream_figure(width=width, height=height, t_seconds=t_seconds)
        print(f"ADAPTER: build_stream_figure returned type={type(fig)}", file=sys.stderr)

        if fig is None:
            raise RuntimeError("adapter returned None")

        # Якщо Plotly-figure-like
        if hasattr(fig, "to_dict") or hasattr(fig, "data"):
            img_bytes = pio.to_image(fig, format="png", width=width, height=height)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((width, height))
        elif isinstance(fig, Image.Image):
            img = fig.convert("RGB").resize((width, height))
        else:
            raise RuntimeError(f"unsupported adapter return type: {type(fig)}")

        # статистика кадру
        arr = np.array(img, dtype=np.uint8)
        md5 = hashlib.md5(arr.tobytes()).hexdigest()
        std = float(arr.std())
        mean = float(arr.mean())
        print(f"ADAPTER: frame md5={md5[:8]} std={std:.3f} mean={mean:.1f} t={t_seconds:.2f}", file=sys.stderr)

        # зберігати кожен 75-ий кадр для візуальної перевірки (регулюйте)
        frame_counter = getattr(render_frame, "_counter", 0) + 1
        render_frame._counter = frame_counter
        if frame_counter % 75 == 0:
            fname = f"frame_debug_{frame_counter}.png"
            img.save(fname)
            print(f"ADAPTER: saved debug frame {fname}", file=sys.stderr)

        return arr

    except Exception as e:
        # лог помилки
        import traceback
        print("ADAPTER ERROR in render_frame:", e, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        # fallback image (як у вас було)
        img = Image.new("RGB", (width, height), (18, 18, 28))
        draw = ImageDraw.Draw(img)
        txt = f"time: {t_seconds:.1f}s (fallback)"
        draw.text((10, 8), txt, fill=(240,240,240))
        cx = int(width/2 + (width/4) * np.sin(t_seconds))
        cy = height//2
        r = 40
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(200,80,80), width=4)
        arr = np.array(img, dtype=np.uint8)
        # також збережемо пробний fallback кадр для аналізу
        try:
            Image.fromarray(arr).save("frame_debug_fallback.png")
            print("Saved frame_debug_fallback.png", file=sys.stderr)
        except Exception:
            pass
        return arr
