import reflex as rx
from app.states.auth_state import AuthState
from app.states.parcel_state import ParcelState
from app.states.sensor_state import SensorState
from app.states.dashboard_state import DashboardState
from app.states.sensor_history_state import SensorHistoryState
from app.states.alert_state import AlertState
from app.components.login_form import login_form
from app.pages.dashboard import dashboard
from app.pages.parcels import parcels_page
from app.pages.parcel_detail import parcel_detail_page
from app.pages.sensor_detail import sensor_detail_page
from app.pages.alerts import alerts_page
from app.api.routes import router as api_router


def login_page() -> rx.Component:
    return login_form()


def dashboard_page() -> rx.Component:
    return dashboard()


def index() -> rx.Component:
    """Redirect root to dashboard (which will redirect to login if needed)."""
    return rx.el.div(rx.script("window.location.href = '/dashboard'"))


def api_routes(api_app):
    for route in api_router.routes:
        path = f"{api_router.prefix}{route.path}"
        api_app.add_route(path, route.endpoint, methods=route.methods)
    return api_app


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
    api_transformer=api_routes,
)
app.add_page(index, route="/")
app.add_page(
    login_page,
    route="/login",
    title="Login - Agrotech",
    on_load=AuthState.ensure_db_seeded,
)
app.add_page(
    dashboard_page,
    route="/dashboard",
    title="Dashboard - Agrotech",
    on_load=[
        AuthState.ensure_db_seeded,
        DashboardState.load_dashboard_stats,
        DashboardState.start_polling,
    ],
)
app.add_page(
    parcels_page,
    route="/parcels",
    title="Parcels - Agrotech",
    on_load=[AuthState.ensure_db_seeded, ParcelState.load_parcels],
)
app.add_page(
    parcel_detail_page,
    route="/parcels/[id]",
    title="Parcel Detail - Agrotech",
    on_load=[AuthState.ensure_db_seeded, SensorState.load_sensors],
)
app.add_page(
    sensor_detail_page,
    route="/sensors/[id]",
    title="Sensor Analysis - Agrotech",
    on_load=[AuthState.ensure_db_seeded, SensorHistoryState.load_history],
)
app.add_page(
    alerts_page,
    route="/alerts",
    title="Alerts - Agrotech",
    on_load=[AuthState.ensure_db_seeded, AlertState.load_alerts],
)