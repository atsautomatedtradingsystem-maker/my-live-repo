# live_stream_adapter.py
"""
Адаптер: повертає plotly Figure або PIL.Image з динамікою.
Якщо у вас є функції у live.py — адаптуйте виклики всередині build_stream_figure.
"""
def build_stream_figure(width=640, height=360, t_seconds=0.0):
    try:
        import plotly.graph_objs as go
        import math
    except Exception:
        # fallback -> PIL image (якщо plotly не встановлено)
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (width, height), (18, 18, 28))
            d = ImageDraw.Draw(img)
            d.text((10,10), f"fallback t={t_seconds:.1f}s", fill=(240,240,240))
            cx = int(width/2 + (width/3) * math.sin(t_seconds*2))
            cy = height//2
            r = 20
            d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(200,80,80), width=4)
            return img
        except Exception:
            return None

    # Простий plotly графік з видимою динамікою
    x = list(range(20))
    y = [((i + t_seconds*2) % 10) for i in x]
    fig = go.Figure(data=[go.Scatter(x=x, y=y, mode="lines+markers")])
    fig.update_layout(width=width, height=height,
                      margin=dict(l=6,r=6,t=24,b=6),
                      paper_bgcolor="#121212", plot_bgcolor="#121212",
                      font=dict(color="#ffffff"))
    fig.add_annotation(text=f"t={t_seconds:.1f}s", x=0.01, y=0.98, xref="paper", yref="paper",
                       showarrow=False, font=dict(size=12,color="#aaaaaa"))
    return fig
