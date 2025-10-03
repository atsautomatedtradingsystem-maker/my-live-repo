# live_stream_adapter.py
def build_stream_figure(width=640, height=360):
    try:
        import importlib
        import plotly.graph_objects as go
        live = None
        try:
            live = importlib.import_module("live")
        except Exception:
            live = None

        if live and hasattr(live, "build_stream_figure"):
            try:
                return live.build_stream_figure(width=width, height=height)
            except Exception:
                pass

        fig = go.Figure()
        fig.update_layout(
            width=width, height=height,
            paper_bgcolor="#121212", plot_bgcolor="#121212",
            margin=dict(l=8,r=8,t=24,b=8), font=dict(color="white")
        )
        import datetime
        fig.add_annotation(text="Stream (adapter)", xref="paper", yref="paper",
                           x=0.02, y=0.98, showarrow=False)
        fig.add_annotation(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           xref="paper", yref="paper", x=0.02, y=0.92, showarrow=False, font=dict(size=10))
        x = list(range(10))
        y = [ (i+1) * (1 + 0.1 * i) for i in x ]
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", marker=dict(size=6)))
        return fig
    except Exception:
        return None
