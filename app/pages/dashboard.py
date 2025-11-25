import reflex as rx
from app.states.auth_state import AuthState
from app.states.dashboard_state import DashboardState
from app.components.styles import M3Styles
from app.components.navbar import navbar


def summary_card(
    title: str, value: str, icon: str, color_class: str, sub_text: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name=f"w-6 h-6 {color_class}"),
            rx.el.div(
                rx.el.p(title, class_name="text-sm font-medium text-slate-500"),
                rx.el.p(value, class_name="text-2xl font-bold text-slate-800 mt-1"),
            ),
            class_name="flex items-start justify-between",
        ),
        rx.el.div(
            rx.el.span(sub_text, class_name="text-xs text-slate-400 font-medium"),
            class_name="mt-4 pt-3 border-t border-slate-50",
        ),
        class_name=f"{M3Styles.CARD}",
    )


def sensor_status_card(sensor: dict) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        sensor["type"],
                        class_name="text-[10px] uppercase tracking-wider font-bold text-slate-400 bg-slate-50 px-2 py-1 rounded-md",
                    ),
                    rx.el.span(
                        rx.cond(
                            sensor["status"] == "green",
                            rx.el.div(class_name="w-2 h-2 rounded-full bg-green-500"),
                            rx.el.div(
                                class_name="w-2 h-2 rounded-full bg-red-500 animate-pulse"
                            ),
                        ),
                        class_name="flex h-6 items-center",
                    ),
                    class_name="flex justify-between items-start mb-3",
                ),
                rx.el.h4(
                    sensor["code"], class_name="text-sm font-bold text-slate-700 mb-1"
                ),
                rx.el.div(
                    rx.el.span(
                        sensor["value"],
                        class_name=rx.cond(
                            sensor["status"] == "green",
                            "text-2xl font-bold text-slate-800",
                            "text-2xl font-bold text-red-600",
                        ),
                    ),
                    rx.el.span(
                        sensor["unit"],
                        class_name="text-sm text-slate-400 ml-1 font-medium mb-1",
                    ),
                    class_name="flex items-end",
                ),
                rx.el.p(
                    f"Updated: {sensor['last_update']}",
                    class_name="text-xs text-slate-400 mt-3",
                ),
            ),
            class_name=f"{M3Styles.CARD} hover:shadow-md transition-all hover:border-blue-200 h-full",
        ),
        href=f"/sensors/{sensor['id']}",
        class_name="block",
    )


def alert_item(alert: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("flag_triangle_right", class_name="w-5 h-5 text-red-500 mr-3"),
                rx.el.div(
                    rx.el.p(
                        alert["sensor_code"],
                        class_name="text-sm font-bold text-slate-700",
                    ),
                    rx.el.p(alert["message"], class_name="text-xs text-slate-500"),
                ),
                class_name="flex items-start flex-1",
            ),
            rx.el.div(
                rx.el.span(alert["time_ago"], class_name="text-xs text-slate-400 mr-3"),
                rx.el.button(
                    "Ack",
                    on_click=lambda: DashboardState.acknowledge_alert(alert["id"]),
                    class_name="text-xs font-medium text-blue-600 hover:bg-blue-50 px-2 py-1 rounded-md transition-colors",
                ),
                class_name="flex items-center",
            ),
            class_name="flex justify-between items-center w-full",
        ),
        class_name="border-b border-slate-50 last:border-0 py-3",
    )


def dashboard_content() -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        f"Dashboard Overview",
                        class_name=f"text-2xl font-bold text-slate-800 mb-1 {M3Styles.FONT_FAMILY}",
                    ),
                    rx.el.p(
                        f"Welcome back, {AuthState.user_name}. System is monitoring in real-time.",
                        class_name="text-slate-500",
                    ),
                    class_name="mb-8",
                ),
                rx.el.div(
                    summary_card(
                        "Total Parcels",
                        AuthState.user_role.to_string(),
                        "map",
                        "text-blue-600",
                        "Active monitoring zones",
                    ),
                    summary_card(
                        "Active Sensors",
                        DashboardState.total_sensors.to_string(),
                        "activity",
                        "text-purple-600",
                        "Telemetry devices online",
                    ),
                    summary_card(
                        "System Alerts",
                        DashboardState.active_alerts.to_string(),
                        "bell",
                        "text-red-500",
                        "Requires attention",
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.h3(
                                "Live Telemetry",
                                class_name="text-lg font-bold text-slate-800",
                            ),
                            rx.el.div(
                                rx.el.div(
                                    class_name="w-2 h-2 rounded-full bg-green-500 animate-pulse"
                                ),
                                rx.el.span(
                                    "Live Updates",
                                    class_name="text-xs font-medium text-green-700",
                                ),
                                class_name="flex items-center gap-2 bg-green-50 px-3 py-1 rounded-full",
                            ),
                            class_name="flex justify-between items-center mb-6",
                        ),
                        rx.el.div(
                            rx.foreach(
                                DashboardState.sensor_statuses, sensor_status_card
                            ),
                            class_name="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4",
                        ),
                        class_name="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 mb-6",
                    ),
                    rx.cond(
                        DashboardState.active_alerts > 0,
                        rx.el.div(
                            rx.el.div(
                                rx.el.h3(
                                    "Active Alerts",
                                    class_name="text-lg font-bold text-slate-800",
                                ),
                                rx.el.a(
                                    "View All",
                                    href="/alerts",
                                    class_name="text-sm text-blue-600 hover:underline",
                                ),
                                class_name="flex justify-between items-center mb-4",
                            ),
                            rx.el.div(
                                rx.foreach(
                                    DashboardState.active_alerts_list, alert_item
                                )
                            ),
                            class_name="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 border-l-4 border-l-red-500",
                        ),
                    ),
                    class_name="flex flex-col gap-6",
                ),
                class_name="max-w-7xl mx-auto px-4 py-8",
            ),
            class_name="bg-slate-50 min-h-[calc(100vh-64px)]",
        ),
        class_name=f"min-h-screen w-full {M3Styles.FONT_FAMILY}",
    )


def dashboard() -> rx.Component:
    return dashboard_content()