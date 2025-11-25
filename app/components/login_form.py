import reflex as rx
from app.states.auth_state import AuthState
from app.components.styles import M3Styles


def login_form() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("sprout", class_name="w-12 h-12 text-blue-600 mb-4"),
                rx.el.h1(
                    "Welcome Back",
                    class_name=f"text-3xl font-bold text-slate-800 mb-2 {M3Styles.FONT_FAMILY}",
                ),
                rx.el.p(
                    "Sign in to access your Agrotech Dashboard",
                    class_name="text-slate-500 mb-8 font-medium",
                ),
                class_name="flex flex-col items-center text-center",
            ),
            rx.el.form(
                rx.el.div(
                    rx.el.label(
                        "Username",
                        class_name="text-sm font-semibold text-slate-700 ml-1 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="e.g., admin",
                        name="username",
                        class_name=M3Styles.INPUT_FIELD,
                        default_value=AuthState.username,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Password",
                        class_name="text-sm font-semibold text-slate-700 ml-1 mb-1 block",
                    ),
                    rx.el.input(
                        type="password",
                        placeholder="••••••••",
                        name="password",
                        class_name=M3Styles.INPUT_FIELD,
                        default_value=AuthState.password,
                    ),
                    class_name="mb-6",
                ),
                rx.cond(
                    AuthState.error_message != "",
                    rx.el.div(
                        rx.icon("badge_alert", class_name="w-5 h-5"),
                        rx.el.p(AuthState.error_message),
                        class_name=f"flex items-center gap-2 p-3 mb-6 {M3Styles.ROUNDED_MD} {M3Styles.ERROR} {M3Styles.ON_ERROR} bg-opacity-90 text-sm font-medium",
                    ),
                ),
                rx.el.button(
                    rx.cond(
                        AuthState.is_loading,
                        rx.spinner(size="2", color="white"),
                        rx.el.span("Sign In"),
                    ),
                    rx.cond(
                        AuthState.is_loading,
                        None,
                        rx.icon("arrow-right", class_name="w-5 h-5"),
                    ),
                    type="submit",
                    disabled=AuthState.is_loading,
                    class_name=f"{M3Styles.BUTTON_PRIMARY} w-full disabled:opacity-70 disabled:cursor-not-allowed",
                ),
                on_submit=AuthState.check_login,
            ),
            rx.el.div(
                rx.el.p(
                    "Demo Credentials:",
                    class_name="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.span("Farmer: ", class_name="text-slate-600 font-bold"),
                        rx.el.span(
                            "admin / admin123", class_name="text-slate-500 font-mono"
                        ),
                        class_name="text-xs",
                    ),
                    rx.el.div(
                        rx.el.span("Tech: ", class_name="text-slate-600 font-bold"),
                        rx.el.span(
                            "tech / tech123", class_name="text-slate-500 font-mono"
                        ),
                        class_name="text-xs",
                    ),
                    class_name="bg-slate-50 p-3 rounded-lg border border-slate-100 w-full",
                ),
                class_name="mt-8 text-center w-full",
            ),
            class_name=f"w-full max-w-md {M3Styles.CARD} {M3Styles.ELEVATION_3}",
        ),
        class_name="min-h-screen w-full flex items-center justify-center bg-slate-50 p-4 relative overflow-hidden",
    )