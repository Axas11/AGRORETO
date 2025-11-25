import reflex as rx
from app.states.auth_state import AuthState
from app.states.sensor_state import SensorState
from app.components.navbar import navbar
from app.components.styles import M3Styles


def sensor_card(sensor: dict) -> rx.Component:
    return rx.el.div(
        rx.el.a(
            rx.el.div(
                rx.el.div(
                    rx.icon("activity", class_name="w-6 h-6 text-purple-600 mb-2"),
                    rx.el.h3(
                        sensor["id_code"], class_name="text-lg font-bold text-slate-800"
                    ),
                    rx.el.p(sensor["description"], class_name="text-sm text-slate-500"),
                    class_name="flex flex-col",
                ),
                rx.el.div(
                    rx.el.span(
                        sensor["type"],
                        class_name="text-xs uppercase font-bold tracking-wider text-slate-400 bg-slate-100 px-2 py-1 rounded-md mt-2 inline-block",
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.span("Range:", class_name="text-xs text-slate-400 mr-2"),
                        rx.el.span(
                            f"{sensor['threshold_low']} - {sensor['threshold_high']} {sensor['unit']}",
                            class_name="text-sm font-mono text-slate-600",
                        ),
                        class_name="flex items-center",
                    ),
                    rx.cond(
                        AuthState.is_farmer,
                        rx.el.button(
                            "Delete",
                            on_click=lambda: SensorState.delete_sensor(sensor["id"]),
                            class_name="text-red-500 text-xs hover:text-red-700 hover:underline mt-2 z-10 relative",
                        ),
                    ),
                    class_name="mt-4 pt-4 border-t border-slate-100 flex justify-between items-end",
                ),
                class_name="flex flex-col h-full",
            ),
            class_name=f"{M3Styles.CARD} hover:shadow-md transition-shadow block h-full",
            href=f"/sensors/{sensor['id']}",
        )
    )


def add_sensor_modal() -> rx.Component:
    return rx.cond(
        SensorState.show_add_sensor_modal,
        rx.el.div(
            rx.el.div(
                rx.el.h3("Add Sensor", class_name="text-xl font-bold mb-4"),
                rx.el.div(
                    rx.el.label(
                        "ID Code",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="e.g. S-TEMP-005",
                        class_name=M3Styles.INPUT_FIELD,
                        on_change=SensorState.set_sensor_code,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Type",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.select(
                        rx.el.option("Temperature", value="temperature"),
                        rx.el.option("Soil Humidity", value="soil_humidity"),
                        rx.el.option("Ambient Humidity", value="ambient_humidity"),
                        rx.el.option("Luminosity", value="luminosity"),
                        class_name=M3Styles.INPUT_FIELD,
                        on_change=SensorState.set_sensor_type,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Description",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="Location description",
                        class_name=M3Styles.INPUT_FIELD,
                        on_change=SensorState.set_sensor_desc,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.label(
                            "Min Threshold",
                            class_name="text-sm font-medium text-slate-700 mb-1 block",
                        ),
                        rx.el.input(
                            type="number",
                            placeholder="0.0",
                            class_name=M3Styles.INPUT_FIELD,
                            on_change=SensorState.set_sensor_low,
                        ),
                        class_name="w-1/2",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Max Threshold",
                            class_name="text-sm font-medium text-slate-700 mb-1 block",
                        ),
                        rx.el.input(
                            type="number",
                            placeholder="100.0",
                            class_name=M3Styles.INPUT_FIELD,
                            on_change=SensorState.set_sensor_high,
                        ),
                        class_name="w-1/2",
                    ),
                    class_name="flex gap-4 mb-6",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=SensorState.toggle_add_modal,
                        class_name="text-slate-600 font-medium px-4 py-2 hover:bg-slate-100 rounded-lg mr-2",
                    ),
                    rx.el.button(
                        "Add Sensor",
                        on_click=SensorState.add_sensor,
                        class_name=f"{M3Styles.BUTTON_PRIMARY} py-2 px-6",
                    ),
                    class_name="flex justify-end",
                ),
                class_name="bg-white p-6 rounded-2xl shadow-xl max-w-md w-full m-4",
            ),
            class_name="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm",
        ),
    )


def parcel_detail_page() -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.a(
                            rx.icon("arrow-left", class_name="w-4 h-4 mr-1"),
                            "Back to Parcels",
                            href="/parcels",
                            class_name="flex items-center text-slate-500 hover:text-blue-600 mb-4 text-sm",
                        ),
                        rx.el.h1(
                            SensorState.parcel_name,
                            class_name=f"text-2xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                        ),
                        rx.el.p(
                            SensorState.parcel_location, class_name="text-slate-500"
                        ),
                    ),
                    rx.cond(
                        AuthState.is_farmer,
                        rx.el.button(
                            rx.icon("plus", class_name="w-5 h-5 mr-2"),
                            "Add Sensor",
                            on_click=SensorState.toggle_add_modal,
                            class_name=f"{M3Styles.BUTTON_PRIMARY} py-2 px-4 text-sm",
                        ),
                    ),
                    class_name="flex justify-between items-end mb-8",
                ),
                rx.cond(
                    SensorState.sensors.length() > 0,
                    rx.el.div(
                        rx.foreach(SensorState.sensors, sensor_card),
                        class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6",
                    ),
                    rx.el.div(
                        rx.icon("sprout", class_name="w-16 h-16 text-slate-200 mb-4"),
                        rx.el.h3(
                            "No Sensors Yet",
                            class_name="text-lg font-medium text-slate-600",
                        ),
                        rx.el.p(
                            "Add sensors to start monitoring this parcel.",
                            class_name="text-slate-500",
                        ),
                        class_name="flex flex-col items-center justify-center py-12 bg-white rounded-2xl border border-slate-100 border-dashed",
                    ),
                ),
                add_sensor_modal(),
                class_name="max-w-7xl mx-auto px-4 py-8",
            ),
            class_name="bg-slate-50 min-h-[calc(100vh-64px)]",
        ),
        class_name=f"min-h-screen w-full {M3Styles.FONT_FAMILY}",
    )