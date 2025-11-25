import reflex as rx
from app.states.auth_state import AuthState
from app.components.styles import M3Styles


def navbar() -> rx.Component:
    return rx.el.nav(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    rx.el.div(
                        rx.icon("sprout", class_name="w-6 h-6 text-blue-600"),
                        rx.el.span(
                            "Agrotech",
                            class_name=f"text-xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                        ),
                        class_name="flex items-center gap-2",
                    ),
                    href="/dashboard",
                ),
                rx.el.div(
                    rx.el.a(
                        "Dashboard",
                        href="/dashboard",
                        class_name="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors",
                    ),
                    rx.el.a(
                        "Parcels",
                        href="/parcels",
                        class_name="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors",
                    ),
                    rx.el.a(
                        "Alerts",
                        href="/alerts",
                        class_name="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors",
                    ),
                    class_name="hidden md:flex items-center gap-6 ml-8",
                ),
                class_name="flex items-center",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        AuthState.user_name, class_name="font-semibold text-slate-700"
                    ),
                    rx.el.span(
                        AuthState.user_role,
                        class_name="text-xs text-slate-500 uppercase bg-slate-100 px-2 py-0.5 rounded-full",
                    ),
                    class_name="flex flex-col items-end mr-4",
                ),
                rx.el.button(
                    rx.icon("log-out", class_name="w-5 h-5"),
                    "Logout",
                    on_click=AuthState.logout,
                    class_name="flex items-center gap-2 text-sm font-medium text-red-600 hover:bg-red-50 px-4 py-2 rounded-full transition-colors",
                ),
                class_name="flex items-center",
            ),
            class_name=f"max-w-7xl mx-auto px-4 h-16 flex items-center justify-between",
        ),
        class_name=f"w-full bg-white border-b border-slate-200 sticky top-0 z-10",
    )