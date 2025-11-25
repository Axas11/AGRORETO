import reflex as rx

TOOLTIP_PROPS = {
    "content_style": {
        "backgroundColor": "white",
        "borderRadius": "8px",
        "border": "1px solid #e2e8f0",
        "boxShadow": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
        "padding": "8px 12px",
    },
    "item_style": {"color": "#475569", "fontSize": "12px", "fontWeight": "500"},
    "label_style": {
        "color": "#1e293b",
        "fontWeight": "600",
        "fontSize": "12px",
        "marginBottom": "4px",
    },
}


def history_chart(data: list[dict], color: str = "#2563eb") -> rx.Component:
    return rx.recharts.line_chart(
        rx.recharts.cartesian_grid(
            stroke_dasharray="3 3", vertical=False, stroke="#e2e8f0"
        ),
        rx.recharts.graphing_tooltip(**TOOLTIP_PROPS),
        rx.recharts.x_axis(
            data_key="time",
            tick_line=False,
            axis_line=False,
            tick={"fontSize": 11, "fill": "#64748b"},
            min_tick_gap=30,
        ),
        rx.recharts.y_axis(
            tick_line=False,
            axis_line=False,
            tick={"fontSize": 11, "fill": "#64748b"},
            domain=["auto", "auto"],
        ),
        rx.recharts.brush(data_key="time", height=30, stroke="#cbd5e1", fill="#f8fafc"),
        rx.recharts.line(
            data_key="value",
            stroke=color,
            stroke_width=2,
            type_="monotone",
            dot=False,
            active_dot={"r": 6, "strokeWidth": 0},
        ),
        data=data,
        width="100%",
        height=300,
        margin={"top": 10, "right": 10, "left": -20, "bottom": 0},
    )