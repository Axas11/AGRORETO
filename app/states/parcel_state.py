import reflex as rx
import logging
from sqlmodel import select, Session
from app.models import Parcel, Sensor
from app.utils import engine
from app.states.auth_state import AuthState


class ParcelState(rx.State):
    parcels: list[Parcel] = []
    selected_parcel_id: int | None = None
    show_add_modal: bool = False
    new_parcel_name: str = ""
    new_parcel_location: str = ""
    new_parcel_area: float = 0.0

    @rx.event
    def load_parcels(self):
        with Session(engine) as session:
            self.parcels = session.exec(select(Parcel)).all()

    @rx.event
    def open_add_modal(self):
        self.show_add_modal = True

    @rx.event
    def close_add_modal(self):
        self.show_add_modal = False
        self.new_parcel_name = ""
        self.new_parcel_location = ""
        self.new_parcel_area = 0.0

    @rx.event
    def set_new_parcel_name(self, value: str):
        self.new_parcel_name = value

    @rx.event
    def set_new_parcel_location(self, value: str):
        self.new_parcel_location = value

    @rx.event
    def set_new_parcel_area(self, value: str):
        try:
            self.new_parcel_area = float(value)
        except ValueError as e:
            logging.exception(f"Error parsing parcel area: {e}")

    @rx.event
    async def add_parcel(self):
        if not self.new_parcel_name or not self.new_parcel_location:
            return
        auth_state = await self.get_state(AuthState)
        if not auth_state.user_id:
            return
        with Session(engine) as session:
            new_parcel = Parcel(
                name=self.new_parcel_name,
                location=self.new_parcel_location,
                area=self.new_parcel_area,
                owner_id=auth_state.user_id,
            )
            session.add(new_parcel)
            session.commit()
            session.refresh(new_parcel)
        self.close_add_modal()
        self.load_parcels()

    @rx.event
    def delete_parcel(self, parcel_id: int):
        with Session(engine) as session:
            parcel = session.get(Parcel, parcel_id)
            if parcel:
                session.delete(parcel)
                session.commit()
        self.load_parcels()

    @rx.event
    def navigate_to_parcel(self, parcel_id: int):
        return rx.redirect(f"/parcels/{parcel_id}")