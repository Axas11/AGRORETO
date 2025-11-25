import reflex as rx
from app.states.auth_state import AuthState
from app.states.parcel_state import ParcelState
from app.components.navbar import navbar
from app.components.styles import M3Styles
from app.models import Parcel


def parcel_card(parcel: Parcel) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon("map-pin", class_name="w-6 h-6 text-blue-600 mb-2"),
                rx.el.h3(parcel.name, class_name="text-lg font-bold text-slate-800"),
                rx.el.p(f"{parcel.area} hectares", class_name="text-sm text-slate-500"),
                rx.el.p(
                    parcel.location, class_name="text-xs text-slate-400 mt-1 font-mono"
                ),
                class_name="flex flex-col items-start",
            ),
            rx.el.div(
                rx.el.button(
                    "Manage Sensors",
                    on_click=lambda: ParcelState.navigate_to_parcel(parcel.id),
                    class_name="text-blue-600 hover:text-blue-800 font-medium text-sm px-3 py-1 rounded-full hover:bg-blue-50 transition-colors",
                ),
                rx.cond(
                    AuthState.is_farmer,
                    rx.el.button(
                        rx.icon("trash-2", class_name="w-4 h-4"),
                        on_click=lambda: ParcelState.delete_parcel(parcel.id),
                        class_name="text-red-400 hover:text-red-600 p-2 hover:bg-red-50 rounded-full transition-colors",
                    ),
                ),
                class_name="flex items-center justify-between w-full mt-4",
            ),
            class_name="flex flex-col justify-between h-full",
        ),
        class_name=f"{M3Styles.CARD} hover:shadow-md transition-shadow cursor-pointer",
    )


def add_parcel_modal() -> rx.Component:
    return rx.cond(
        ParcelState.show_add_modal,
        rx.el.div(
            rx.el.div(
                rx.el.h3("Add New Parcel", class_name="text-xl font-bold mb-4"),
                rx.el.div(
                    rx.el.label(
                        "Name",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="e.g. North Field",
                        class_name=M3Styles.INPUT_FIELD,
                        on_change=ParcelState.set_new_parcel_name,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Location (Coords)",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="e.g. 34.05, -118.24",
                        class_name=M3Styles.INPUT_FIELD,
                        on_change=ParcelState.set_new_parcel_location,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Area (Hectares)",
                        class_name="text-sm font-medium text-slate-700 mb-1 block",
                    ),
                    rx.el.input(
                        type="number",
                        placeholder="e.g. 120.5",
                        class_name=M3Styles.INPUT_FIELD,
                        on_change=ParcelState.set_new_parcel_area,
                    ),
                    class_name="mb-6",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=ParcelState.close_add_modal,
                        class_name="text-slate-600 font-medium px-4 py-2 hover:bg-slate-100 rounded-lg mr-2",
                    ),
                    rx.el.button(
                        "Save Parcel",
                        on_click=ParcelState.add_parcel,
                        class_name=f"{M3Styles.BUTTON_PRIMARY} py-2 px-6",
                    ),
                    class_name="flex justify-end",
                ),
                class_name="bg-white p-6 rounded-2xl shadow-xl max-w-md w-full m-4",
            ),
            class_name="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm",
        ),
    )


def parcels_page() -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.div(
                rx.el.div(
                    rx.el.h1(
                        "My Parcels",
                        class_name=f"text-2xl font-bold text-slate-800 {M3Styles.FONT_FAMILY}",
                    ),
                    rx.cond(
                        AuthState.is_farmer,
                        rx.el.button(
                            rx.icon("plus", class_name="w-5 h-5 mr-2"),
                            "Add Parcel",
                            on_click=ParcelState.open_add_modal,
                            class_name=f"{M3Styles.BUTTON_PRIMARY} py-2 px-4 text-sm",
                        ),
                    ),
                    class_name="flex justify-between items-center mb-8",
                ),
                rx.el.div(
                    rx.foreach(ParcelState.parcels, parcel_card),
                    class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                ),
                add_parcel_modal(),
                class_name="max-w-7xl mx-auto px-4 py-8",
            ),
            class_name="bg-slate-50 min-h-[calc(100vh-64px)]",
        ),
        class_name=f"min-h-screen w-full {M3Styles.FONT_FAMILY}",
    )