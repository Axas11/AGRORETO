import reflex as rx
import logging
from datetime import datetime, timedelta
from sqlmodel import select, Session
from app.models import Sensor, SensorData, Parcel
from app.utils import engine


class SensorHistoryState(rx.State):
    sensor: Sensor | None = None
    parcel_name: str = ""
    history_data: list[dict] = []
    time_range: str = "24h"
    stat_min: float = 0.0
    stat_max: float = 0.0
    stat_avg: float = 0.0

    @rx.var
    def sensor_code(self) -> str:
        return self.sensor.id_code if self.sensor else "Loading..."

    @rx.var
    def sensor_desc(self) -> str:
        return self.sensor.description if self.sensor else ""

    @rx.var
    def sensor_unit(self) -> str:
        return self.sensor.unit if self.sensor else ""

    @rx.var
    def graph_color(self) -> str:
        if not self.sensor:
            return "#3b82f6"
        if self.sensor.type == "temperature":
            return "#ef4444"
        if self.sensor.type == "luminosity":
            return "#eab308"
        return "#3b82f6"

    @rx.var
    def stat_min_str(self) -> str:
        return f"{self.stat_min:.1f}"

    @rx.var
    def stat_max_str(self) -> str:
        return f"{self.stat_max:.1f}"

    @rx.var
    def stat_avg_str(self) -> str:
        return f"{self.stat_avg:.1f}"

    @rx.var
    def sensor_id_param(self) -> int:
        sid_str = self.router.page.params.get("id", "")
        if not sid_str:
            return 0
        try:
            return int(sid_str)
        except ValueError as e:
            logging.exception(f"Error parsing sensor_id_param: {e}")
            return 0

    @rx.event
    def set_time_range(self, value: str):
        self.time_range = value
        self.load_history()

    @rx.event
    def load_history(self):
        self.history_data = []
        self.sensor = None
        sid = self.sensor_id_param
        if not sid:
            return
        with Session(engine) as session:
            self.sensor = session.get(Sensor, sid)
            if self.sensor:
                parcel = session.get(Parcel, self.sensor.parcel_id)
                self.parcel_name = parcel.name if parcel else "Unknown Parcel"
            else:
                self.parcel_name = "Sensor Not Found"
                return
            now = datetime.utcnow()
            if self.time_range == "24h":
                start_time = now - timedelta(hours=24)
            elif self.time_range == "7d":
                start_time = now - timedelta(days=7)
            elif self.time_range == "30d":
                start_time = now - timedelta(days=30)
            else:
                start_time = now - timedelta(days=365)
            query = (
                select(SensorData)
                .where(SensorData.sensor_id == sid, SensorData.timestamp >= start_time)
                .order_by(SensorData.timestamp.asc())
            )
            data_points = session.exec(query).all()
            chart_data = []
            values = []
            for pt in data_points:
                ts_str = (
                    pt.timestamp.strftime("%m-%d %H:%M")
                    if self.time_range != "24h"
                    else pt.timestamp.strftime("%H:%M")
                )
                chart_data.append(
                    {
                        "time": ts_str,
                        "value": pt.value,
                        "raw_ts": pt.timestamp.isoformat(),
                    }
                )
                values.append(pt.value)
            self.history_data = chart_data
            if values:
                self.stat_min = min(values)
                self.stat_max = max(values)
                self.stat_avg = sum(values) / len(values)
            else:
                self.stat_min = 0.0
                self.stat_max = 0.0
                self.stat_avg = 0.0