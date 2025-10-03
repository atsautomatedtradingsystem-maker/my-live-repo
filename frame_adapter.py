# frame_adapter.py
# Використовуйте цей файл як bridge: бере plotly-fig з live.py і повертає RGB numpy масив.
import os, io
os.environ.setdefault("LIVE_HEADLESS", "1")  # допоможе в майбутньому уникнути UI-поведінки
import numpy as np
from PIL import Image

# plotly.io потрібен для конвертації fig->png
import plotly.io as pio

# Імпортуємо live (ваш файл). Імпорт може вимагати встановлених залежностей.
import live

def render_frame_from_live(t_seconds, width=640, height=360):
    """
    Викликає callback/update в live.py, бере plotly Figure і повертає numpy (H,W,3) uint8.
    Якщо щось пішло не так — повертає diagnostic image.
    """
    try:
        # Побудова minimal store, якщо потрібен (live.update очікує store)
        # Це простий приклад — ви можете наповнити store реальними даними якщо потрібно.
        store = {"active_symbol": getattr(getattr(live, 'settings', None), 'symbol', None),
                 "wallets": {}} if hasattr(live, 'settings') else {"wallets": {}}

        # Викликаємо вашу функцію update(n, store) без dash контексту — вона повертає (fig, cards, store) згідно live.py
        # Якщо ваша update має іншу сигнатуру — підставте відповідно.
        res = live.update(0, store)
        # часто update повертає (fig, metrics, store)
        if isinstance(res, (list, tuple)):
            fig = res[0]
        else:
            fig = res

        # Конвертуємо plotly Figure -> PNG bytes (kaleido)
        img_bytes = pio.to_image(fig, format='png', width=width, height=height)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((width, height))
        return np.array(img, dtype=np.uint8)
    except Exception as e:
        # diagnostic image (щоб поток не зламався)
        img = Image.new("RGB", (width, height), (20,20,30))
        d = Image.ImageDraw.Draw(img)
        msg = f"render error: {str(e)[:180]}"
        try:
            d.text((8,8), msg, fill=(255,100,100))
        except Exception:
            pass
        return np.array(img, dtype=np.uint8)
