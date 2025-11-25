import reflex as rx
import logging
from sqlmodel import select, Session
from app.models import Sensor, Parcel
from app.utils import engine


class SensorState(rx.State):
    sensors: list[dict] = []
    current_parcel: Parcel | None = None
    show_add_sensor_modal: bool = False
    new_sensor_code: str = ""
    new_sensor_type: str = "temperature"
    new_sensor_unit: str = "°C"
    new_sensor_desc: str = ""
    new_sensor_low: float = 0.0
    new_sensor_high: float = 100.0

    @rx.var
    def parcel_name(self) -> str:
        return self.current_parcel.name if self.current_parcel else "Loading..."

    @rx.var
    def parcel_location(self) -> str:
        return self.current_parcel.location if self.current_parcel else ""

    @rx.var
    def parcel_id(self) -> int:
        pid_str = self.router.page.params.get("id", "")
        if not pid_str:
            return 0
        try:
            return int(pid_str)
        except ValueError as e:
            logging.exception(f"Error parsing parcel_id: {e}")
            return 0

    @rx.event
    def load_sensors(self):
        self.sensors = []
        self.current_parcel = None
        pid = self.parcel_id
        if not pid:
            return
        with Session(engine) as session:
            self.current_parcel = session.get(Parcel, pid)
            if self.current_parcel:
                sensors_objs = session.exec(
                    select(Sensor).where(Sensor.parcel_id == pid)
                ).all()
                self.sensors = [s.model_dump() for s in sensors_objs]

    @rx.event
    def toggle_add_modal(self):
        self.show_add_sensor_modal = not self.show_add_sensor_modal

    @rx.event
    def set_sensor_code(self, val: str):
        self.new_sensor_code = val

    @rx.event
    def set_sensor_type(self, val: str):
        self.new_sensor_type = val
        if val == "temperature":
            self.new_sensor_unit = "°C"
        elif "humidity" in val:
            self.new_sensor_unit = "%"
        elif "luminosity" in val:
            self.new_sensor_unit = "lux"

    @rx.event
    def set_sensor_unit(self, val: str):
        self.new_sensor_unit = val

    @rx.event
    def set_sensor_desc(self, val: str):
        self.new_sensor_desc = val

    @rx.event
    def set_sensor_low(self, val: str):
        try:
            self.new_sensor_low = float(val)
        except ValueError as e:
            logging.exception(f"Error parsing sensor low threshold: {e}")

    @rx.event
    def set_sensor_high(self, val: str):
        try:
            self.new_sensor_high = float(val)
        except ValueError as e:
            logging.exception(f"Error parsing sensor high threshold: {e}")

    @rx.event
    def add_sensor(self):
        if not self.current_parcel:
            return
        with Session(engine) as session:
            new_sensor = Sensor(
                id_code=self.new_sensor_code,
                parcel_id=self.current_parcel.id,
                type=self.new_sensor_type,
                unit=self.new_sensor_unit,
                description=self.new_sensor_desc,
                threshold_low=self.new_sensor_low,
                threshold_high=self.new_sensor_high,
            )
            session.add(new_sensor)
            session.commit()
        self.toggle_add_modal()
        self.load_sensors()

    @rx.event
    def delete_sensor(self, sensor_id: int):
        with Session(engine) as session:
            sensor = session.get(Sensor, sensor_id)
            if sensor:
                session.delete(sensor)
                session.commit()
        self.load_sensors()