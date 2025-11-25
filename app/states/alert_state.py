import reflex as rx
from sqlmodel import select, Session, desc
from app.models import Alert, Sensor
from app.utils import engine
from datetime import datetime


class AlertState(rx.State):
    alerts: list[dict] = []
    filter_type: str = "all"
    show_history: bool = False

    @rx.event
    def set_filter_type(self, value: str):
        self.filter_type = value
        self.load_alerts()

    @rx.event
    def toggle_history(self, checked: bool):
        self.show_history = checked
        self.load_alerts()

    @rx.event
    def load_alerts(self):
        with Session(engine) as session:
            query = select(Alert)
            if not self.show_history:
                query = query.where(Alert.acknowledged == False)
            if self.filter_type != "all":
                query = query.where(Alert.type == self.filter_type)
            query = query.order_by(desc(Alert.timestamp))
            results = session.exec(query).all()
            display_list = []
            for a in results:
                s = session.get(Sensor, a.sensor_id)
                display_list.append(
                    {
                        "id": a.id,
                        "sensor_code": s.id_code if s else "Unknown",
                        "sensor_type": s.type if s else "",
                        "type": a.type,
                        "message": a.message,
                        "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M"),
                        "acknowledged": a.acknowledged,
                        "color": "red" if a.type == "HIGH" else "amber",
                    }
                )
            self.alerts = display_list

    @rx.event
    def acknowledge_alert(self, alert_id: int):
        with Session(engine) as session:
            alert = session.get(Alert, alert_id)
            if alert:
                alert.acknowledged = True
                session.add(alert)
                session.commit()
        self.load_alerts()
        return rx.toast("Alert acknowledged", duration=3000, close_button=True)