# live_stream_adapter.py
"""
Адаптер для stream_frames.py — намагається отримати plotly-фігуру з live.py
Якщо import live або виклик update() провалюється — повертає None.
stream_frames.py потім робить fallback render.
"""

def build_stream_figure(width=640, height=360):
    """
    ПОВИНЕН ПОВЕРТАТИ:
      - plotly.graph_objs._figure.Figure  (оптимально)
      або
      - PIL.Image.Image
      або
      - None (тоді буде fallback).
    Стратегія:
      1) Спробувати імпортнути live і викликати його callback update(0, store)
      2) Якщо немає update() — шукати helper build_stream_figure у live
    """
    try:
        # імпортуємо модуль live (може кидати ModuleNotFoundError якщо немає deps)
        import importlib
        live = importlib.import_module("live")
    except Exception as e:
        # лог в stderr, але не піднімаємо виняток
        print("ADAPTER: import live failed:", e, file=sys.stderr if 'sys' in globals() else None)
        return None

    try:
        # 1) якщо у live є спеціальна функція build_stream_figure — викликнемо її
        if hasattr(live, "build_stream_figure"):
            try:
                fig = live.build_stream_figure(width=width, height=height)
                return fig
            except Exception as e:
                print("ADAPTER: live.build_stream_figure() failed:", e)
                # падіння — пробуємо далі
        # 2) Інакше — намагаємось викликати основний callback update(n, store)
        if hasattr(live, "update"):
            try:
                # передаємо простий store (можна змінити на потрібний вам)
                store = getattr(live, "active_state", {}) or {}
                res = live.update(0, store)
                # update() за вашим кодом повертає (figure, children, store)
                if isinstance(res, (list, tuple)) and len(res) >= 1:
                    return res[0]
                # якщо update повернув одне значення — повертаємо його
                return res
            except Exception as e:
                print("ADAPTER: live.update() call failed:", e)
                return None
        # нічого не знайшли
        return None
    except Exception as e:
        print("ADAPTER: unexpected error:", e)
        return None
