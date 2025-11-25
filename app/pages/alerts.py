import reflex as rx
from app.states.auth_state import AuthState
from app.states.alert_state import AlertState
from app.components.navbar import navbar
from app.components.styles import M3Styles


def alert_row(alert: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.cond(
                    alert["type"] == "HIGH",
                    rx.icon("trending-up", class_name="w-5 h-5 text-red-500"),
                    rx.icon("trending-down", class_name="w-5 h-5 text-amber-500"),
                ),
                class_name="p-3 bg-slate-50 rounded-full mr-4",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h4(
                        alert["sensor_code"],
                        class_name="text-sm font-bold text-slate-800",
                    ),
                    rx.el.span(
                        alert["sensor_type"],
                        class_name="ml-2 text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full uppercase tracking-wider",
                    ),
                    class_name="flex items-center mb-1",
                ),
                rx.el.p(alert["message"], class_name="text-sm text-slate-600"),
            ),
            class_name="flex items-center flex-1",
        ),
        rx.el.div(
            rx.el.span(
                alert["timestamp"], class_name="text-xs text-slate-400 mr-6 font-mono"
            ),
            rx.cond(
                alert["acknowledged"],
                rx.el.span(
                    "Acknowledged",
                    class_name="text-xs font-bold text-green-600 bg-green-50 px-3 py-1 rounded-full",
                ),
                rx.el.button(
                    "Acknowledge",
                    on_click=lambda: AlertState.acknowledge_alert(alert["id"]),
                    class_name=f"{M3Styles.BUTTON_PRIMARY} py-1.5 px-4 text-xs shadow-none hover:shadow-md",
                ),
            ),
            class_name="flex items-center",
        ),
        class_name=f"{M3Styles.CARD} flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:border-blue-200 transition-colors",
    )


def alerts_page() -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.h1(
                        "Alerts Management",
                        class_name=f"text-2xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                    ),
                    rx.el.p(
                        "Review and manage sensor notifications",
                        class_name="text-slate-500",
                    ),
                    class_name="mb-8",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.select(
                            rx.el.option("All Types", value="all"),
                            rx.el.option("High Value", value="HIGH"),
                            rx.el.option("Low Value", value="LOW"),
                            on_change=AlertState.set_filter_type,
                            class_name="bg-white border border-slate-200 text-slate-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5",
                        ),
                        rx.el.div(
                            rx.el.label(
                                rx.el.input(
                                    type="checkbox",
                                    on_change=AlertState.toggle_history,
                                    class_name="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500",
                                ),
                                rx.el.span(
                                    "Show Acknowledged",
                                    class_name="ml-2 text-sm font-medium text-slate-700",
                                ),
                                class_name="flex items-center",
                            ),
                            class_name="flex items-center ml-4",
                        ),
                        class_name="flex items-center mb-6",
                    ),
                    rx.cond(
                        AlertState.alerts.length() > 0,
                        rx.el.div(
                            rx.foreach(AlertState.alerts, alert_row),
                            class_name="flex flex-col gap-4",
                        ),
                        rx.el.div(
                            rx.icon(
                                "check_check",
                                class_name="w-16 h-16 text-green-200 mb-4",
                            ),
                            rx.el.h3(
                                "No Alerts Found",
                                class_name="text-lg font-medium text-slate-700",
                            ),
                            rx.el.p(
                                "System is running within normal parameters.",
                                class_name="text-slate-500",
                            ),
                            class_name="flex flex-col items-center justify-center py-16 bg-white rounded-2xl border border-slate-100 border-dashed",
                        ),
                    ),
                ),
                class_name="max-w-7xl mx-auto px-4 py-8",
            ),
            class_name="bg-slate-50 min-h-[calc(100vh-64px)]",
        ),
        class_name=f"min-h-screen w-full {M3Styles.FONT_FAMILY}",
    )