import reflex as rx
from app.states.auth_state import AuthState
from app.states.sensor_history_state import SensorHistoryState
from app.components.navbar import navbar
from app.components.styles import M3Styles
from app.components.charts import history_chart


def stat_box(label: str, value: str, unit: str) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="text-xs font-medium text-slate-500 uppercase tracking-wider",
        ),
        rx.el.div(
            rx.el.span(value, class_name="text-xl font-bold text-slate-800"),
            rx.el.span(unit, class_name="text-xs text-slate-400 ml-1 font-medium"),
            class_name="mt-1",
        ),
        class_name="bg-slate-50 p-4 rounded-xl border border-slate-100",
    )


def range_button(label: str, value: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=lambda: SensorHistoryState.set_time_range(value),
        class_name=rx.cond(
            SensorHistoryState.time_range == value,
            f"{M3Styles.PRIMARY} {M3Styles.ON_PRIMARY} px-4 py-1.5 rounded-lg text-sm font-medium shadow-sm",
            "bg-white text-slate-600 hover:bg-slate-50 px-4 py-1.5 rounded-lg text-sm font-medium border border-slate-200",
        ),
    )


def sensor_detail_page() -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.a(
                        rx.icon("arrow-left", class_name="w-4 h-4 mr-1"),
                        "Back to Dashboard",
                        href="/dashboard",
                        class_name="flex items-center text-slate-500 hover:text-blue-600 mb-4 text-sm",
                    ),
                    rx.cond(
                        SensorHistoryState.sensor_code != "Loading...",
                        rx.el.div(
                            rx.el.div(
                                rx.el.div(
                                    rx.el.h1(
                                        SensorHistoryState.sensor_code,
                                        class_name=f"text-2xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                                    ),
                                    rx.el.p(
                                        SensorHistoryState.sensor_desc,
                                        class_name="text-slate-500",
                                    ),
                                ),
                                rx.el.div(
                                    rx.icon(
                                        "map-pin",
                                        class_name="w-4 h-4 text-slate-400 mr-1",
                                    ),
                                    rx.el.span(
                                        SensorHistoryState.parcel_name,
                                        class_name="text-sm font-medium text-slate-600",
                                    ),
                                    class_name="flex items-center bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm",
                                ),
                                class_name="flex justify-between items-start mb-8",
                            ),
                            rx.el.div(
                                rx.el.div(
                                    rx.el.h3(
                                        "Historical Analysis",
                                        class_name="text-lg font-bold text-slate-800",
                                    ),
                                    rx.el.div(
                                        range_button("24h", "24h"),
                                        range_button("7 Days", "7d"),
                                        range_button("30 Days", "30d"),
                                        class_name="flex gap-2",
                                    ),
                                    class_name="flex justify-between items-center mb-6",
                                ),
                                rx.el.div(
                                    rx.cond(
                                        SensorHistoryState.history_data.length() > 0,
                                        history_chart(
                                            SensorHistoryState.history_data,
                                            SensorHistoryState.graph_color,
                                        ),
                                        rx.el.div(
                                            "No data points available for this range.",
                                            class_name="flex items-center justify-center h-full text-slate-400 text-sm",
                                        ),
                                    ),
                                    class_name="w-full h-[300px]",
                                ),
                                class_name=f"{M3Styles.CARD} mb-6",
                            ),
                            rx.el.div(
                                stat_box(
                                    "Minimum",
                                    SensorHistoryState.stat_min_str,
                                    SensorHistoryState.sensor_unit,
                                ),
                                stat_box(
                                    "Average",
                                    SensorHistoryState.stat_avg_str,
                                    SensorHistoryState.sensor_unit,
                                ),
                                stat_box(
                                    "Maximum",
                                    SensorHistoryState.stat_max_str,
                                    SensorHistoryState.sensor_unit,
                                ),
                                class_name="grid grid-cols-1 md:grid-cols-3 gap-6",
                            ),
                        ),
                        rx.el.div(
                            rx.spinner(size="3"),
                            class_name="flex justify-center items-center h-64",
                        ),
                    ),
                ),
                class_name="max-w-5xl mx-auto px-4 py-8",
            ),
            class_name="bg-slate-50 min-h-[calc(100vh-64px)]",
        ),
        class_name=f"min-h-screen w-full {M3Styles.FONT_FAMILY}",
    )