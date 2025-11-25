import reflex as rx
import asyncio
from datetime import datetime
from sqlmodel import select, func, Session
from app.models import Parcel, Sensor, SensorData, Alert
from app.utils import engine


class DashboardState(rx.State):
    total_sensors: int = 0
    active_alerts: int = 0
    total_parcels: int = 0
    sensor_statuses: list[dict] = []
    active_alerts_list: list[dict] = []
    is_polling: bool = False

    def _get_latest_reading(self, session, sensor_id):
        return session.exec(
            select(SensorData)
            .where(SensorData.sensor_id == sensor_id)
            .order_by(SensorData.timestamp.desc())
            .limit(1)
        ).first()

    @rx.event
    def load_dashboard_stats(self):
        with Session(engine) as session:
            self.total_sensors = session.exec(select(func.count(Sensor.id))).one()
            self.total_parcels = session.exec(select(func.count(Parcel.id))).one()
            sensors = session.exec(select(Sensor)).all()
            status_list = []
            for sensor in sensors:
                latest = self._get_latest_reading(session, sensor.id)
                status = "gray"
                value_display = "--"
                last_update = "Never"
                if latest:
                    val = latest.value
                    value_display = f"{val:.1f}"
                    violation_type = None
                    msg = ""
                    if val < sensor.threshold_low:
                        status = "red"
                        violation_type = "LOW"
                        msg = f"Value {val:.1f} {sensor.unit} is below minimum threshold {sensor.threshold_low} {sensor.unit}"
                    elif val > sensor.threshold_high:
                        status = "red"
                        violation_type = "HIGH"
                        msg = f"Value {val:.1f} {sensor.unit} is above maximum threshold {sensor.threshold_high} {sensor.unit}"
                    else:
                        status = "green"
                    if violation_type:
                        existing = session.exec(
                            select(Alert)
                            .where(Alert.sensor_id == sensor.id)
                            .where(Alert.type == violation_type)
                            .where(Alert.acknowledged == False)
                        ).first()
                        if not existing:
                            new_alert = Alert(
                                sensor_id=sensor.id,
                                type=violation_type,
                                message=msg,
                                timestamp=latest.timestamp,
                            )
                            session.add(new_alert)
                            session.commit()
                    diff = datetime.utcnow() - latest.timestamp
                    if diff.total_seconds() < 60:
                        last_update = "Just now"
                    elif diff.total_seconds() < 3600:
                        last_update = f"{int(diff.total_seconds() / 60)}m ago"
                    else:
                        last_update = f"{int(diff.total_seconds() / 3600)}h ago"
                status_list.append(
                    {
                        "id": sensor.id,
                        "code": sensor.id_code,
                        "type": sensor.type,
                        "value": value_display,
                        "unit": sensor.unit,
                        "status": status,
                        "last_update": last_update,
                        "parcel_id": sensor.parcel_id,
                    }
                )
            self.sensor_statuses = status_list
            self.active_alerts = session.exec(
                select(func.count(Alert.id)).where(Alert.acknowledged == False)
            ).one()
            alerts = session.exec(
                select(Alert)
                .where(Alert.acknowledged == False)
                .order_by(Alert.timestamp.desc())
                .limit(5)
            ).all()
            alerts_display = []
            for a in alerts:
                s = session.get(Sensor, a.sensor_id)
                diff = datetime.utcnow() - a.timestamp
                if diff.total_seconds() < 3600:
                    time_ago = f"{int(diff.total_seconds() / 60)}m ago"
                elif diff.total_seconds() < 86400:
                    time_ago = f"{int(diff.total_seconds() / 3600)}h ago"
                else:
                    time_ago = f"{int(diff.days)}d ago"
                alerts_display.append(
                    {
                        "id": a.id,
                        "sensor_code": s.id_code if s else "Unknown",
                        "type": a.type,
                        "message": a.message,
                        "time_ago": time_ago,
                    }
                )
            self.active_alerts_list = alerts_display

    @rx.event
    def acknowledge_alert(self, alert_id: int):
        with Session(engine) as session:
            alert = session.get(Alert, alert_id)
            if alert:
                alert.acknowledged = True
                session.add(alert)
                session.commit()
        self.load_dashboard_stats()
        return rx.toast("Alert acknowledged", duration=3000, close_button=True)

    @rx.event(background=True)
    async def start_polling(self):
        """Start background polling for dashboard updates."""
        async with self:
            if self.is_polling:
                return
            self.is_polling = True
        while True:
            async with self:
                if not self.is_polling:
                    break
                self.load_dashboard_stats()
            await asyncio.sleep(5)

    @rx.event
    def stop_polling(self):
        self.is_polling = False