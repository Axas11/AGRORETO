# app/pages/parcel_detail.py
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
    """Modal mejorado con campo MQTT Topic"""
    return rx.cond(
        SensorState.show_add_sensor_modal,
        rx.el.div(
            rx.el.div(
                rx.el.h3("Add Sensor", class_name="text-xl font-bold mb-4"),
                
                # ID Code
                rx.el.div(
                    rx.el.label(
                        "ID Code",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="e.g. S-TEMP-005",
                        value=SensorState.new_sensor_code,
                        class_name=M3Styles.INPUT_FIELD,
                        on_change=SensorState.set_sensor_code,
                    ),
                    class_name="mb-4",
                ),
                
                # Type
                rx.el.div(
                    rx.el.label(
                        "Type",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.select(
                        rx.el.option("Temperature", value="temperature"),
                        rx.el.option("Soil Humidity", value="humidity_soil"),
                        rx.el.option("Ambient Humidity", value="humidity_ambient"),
                        rx.el.option("Luminosity", value="luminosity"),
                        rx.el.option("CO2", value="co2"),
                        rx.el.option("COV", value="cov"),
                        rx.el.option("NOx", value="nox"),
                        class_name=M3Styles.INPUT_FIELD,
                        value=SensorState.new_sensor_type,
                        on_change=SensorState.set_sensor_type,
                    ),
                    class_name="mb-4",
                ),
                
                # Description
                rx.el.div(
                    rx.el.label(
                        "Description",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="Location description",
                        value=SensorState.new_sensor_desc,
                        class_name=M3Styles.INPUT_FIELD,
                        on_change=SensorState.set_sensor_desc,
                    ),
                    class_name="mb-4",
                ),
                
                # MQTT Topic (NUEVO)
                rx.el.div(
                    rx.el.label(
                        "MQTT Topic",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="Awi7LJfyyn6LPjg/15046220",
                        value=SensorState.new_sensor_mqtt_topic,
                        class_name=M3Styles.INPUT_FIELD,
                        on_change=SensorState.set_sensor_mqtt_topic,
                    ),
                    rx.el.p(
                        "Topic del sensor MAIoTA en EMQX broker",
                        class_name="text-xs text-slate-400 mt-1"
                    ),
                    class_name="mb-4",
                ),
                
                # Thresholds
                rx.el.div(
                    rx.el.div(
                        rx.el.label(
                            "Min Threshold",
                            class_name="text-sm font-medium text-slate-700 mb-1 block",
                        ),
                        rx.el.input(
                            type="number",
                            placeholder="0.0",
                            value=SensorState.new_sensor_low,
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
                            value=SensorState.new_sensor_high,
                            class_name=M3Styles.INPUT_FIELD,
                            on_change=SensorState.set_sensor_high,
                        ),
                        class_name="w-1/2",
                    ),
                    class_name="flex gap-4 mb-6",
                ),
                
                # Botones
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
    """Página principal de detalle de parcela con sensores"""
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.div(
                # Breadcrumb
                rx.el.a(
                    rx.icon("arrow-left", class_name="w-4 h-4 mr-1"),
                    "Back to Parcels",
                    href="/parcels",
                    class_name="flex items-center text-slate-500 hover:text-blue-600 mb-4 text-sm",
                ),
                
                # Header con info de parcela
                rx.el.div(
                    rx.el.div(
                        rx.el.h1(
                            SensorState.parcel_name,
                            class_name=f"text-2xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                        ),
                        rx.el.p(
                            SensorState.parcel_location,
                            class_name="text-slate-500",
                        ),
                    ),
                    rx.cond(
                        AuthState.is_farmer,
                        rx.el.button(
                            rx.icon("plus", class_name="w-4 h-4 mr-1"),
                            "Add Sensor",
                            on_click=SensorState.toggle_add_modal,
                            class_name=f"{M3Styles.BUTTON_PRIMARY} flex items-center",
                        ),
                    ),
                    class_name="flex justify-between items-start mb-8",
                ),
                
                # Grid de sensores
                rx.cond(
                    SensorState.sensors.length() > 0,
                    rx.el.div(
                        rx.foreach(
                            SensorState.sensors,
                            sensor_card,
                        ),
                        class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                    ),
                    rx.el.div(
                        rx.icon("inbox", class_name="w-12 h-12 text-slate-300 mb-2"),
                        rx.el.p(
                            "No sensors yet",
                            class_name="text-slate-400 text-sm",
                        ),
                        class_name="flex flex-col items-center justify-center py-16",
                    ),
                ),
                
                class_name="max-w-7xl mx-auto px-4 py-8",
            ),
            class_name="bg-slate-50 min-h-[calc(100vh-64px)]",
        ),
        
        # Modal
        add_sensor_modal(),
        
        class_name=f"min-h-screen w-full {M3Styles.FONT_FAMILY}",
    )
