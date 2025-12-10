# app/states/dashboard_state.py
import asyncio
from datetime import datetime

import reflex as rx
from sqlmodel import Session, func, select

from app.models import Alert, Parcel, ParcelTechnician, Sensor, SensorData
from app.states.auth_state import AuthState
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
    async def load_dashboard_stats(self):
        """Carga estadísticas del dashboard según permisos del usuario"""
        # ✅ Obtener info del usuario
        auth_state = await self.get_state(AuthState)
        user_role = auth_state.user_role
        user_id = auth_state.user_id
        
        if not user_id:
            self.sensor_statuses = []
            self.active_alerts_list = []
            return

        with Session(engine) as session:
            # ✅ Determinar parcelas accesibles
            if user_role == "farmer":
                # Farmers ven todas las parcelas
                accessible_parcels = session.exec(select(Parcel)).all()
            else:
                # Técnicos: parcelas propias + asignadas
                assigned_parcel_ids = session.exec(
                    select(ParcelTechnician.parcel_id).where(
                        ParcelTechnician.user_id == user_id
                    )
                ).all()
                
                if assigned_parcel_ids:
                    accessible_parcels = session.exec(
                        select(Parcel).where(
                            (Parcel.owner_id == user_id) | 
                            (Parcel.id.in_(assigned_parcel_ids))
                        )
                    ).all()
                else:
                    accessible_parcels = session.exec(
                        select(Parcel).where(Parcel.owner_id == user_id)
                    ).all()
            
            parcel_ids = [p.id for p in accessible_parcels]
            
            if not parcel_ids:
                self.total_sensors = 0
                self.total_parcels = 0
                self.sensor_statuses = []
                self.active_alerts = 0
                self.active_alerts_list = []
                return
            
            # ✅ Contar solo parcelas y sensores accesibles
            self.total_parcels = len(parcel_ids)
            
            # ✅ Obtener sensores de parcelas accesibles
            sensors = session.exec(
                select(Sensor).where(Sensor.parcel_id.in_(parcel_ids))
            ).all()
            
            self.total_sensors = len(sensors)
            
            status_list = []
            for sensor in sensors:
                latest = self._get_latest_reading(session, sensor.id)
                status = "gray"
                value_display = "--"
                last_update = "Nunca"
                
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
                    
                    diff = datetime.now() - latest.timestamp
                    if diff.total_seconds() < 60:
                        last_update = "Justo ahora"
                    elif diff.total_seconds() < 3600:
                        last_update = f"{int(diff.total_seconds() / 60)}m atrás"
                    else:
                        last_update = f"{int(diff.total_seconds() / 3600)}h atrás"
                
                status_list.append({
                    "id": sensor.id,
                    "code": sensor.id_code,
                    "type": sensor.type,
                    "value": value_display,
                    "unit": sensor.unit,
                    "status": status,
                    "last_update": last_update,
                    "parcel_id": sensor.parcel_id,
                })
            
            self.sensor_statuses = status_list
            
            # ✅ Alertas solo de sensores accesibles
            sensor_ids = [s.id for s in sensors]
            
            if sensor_ids:
                self.active_alerts = session.exec(
                    select(func.count(Alert.id)).where(
                        (Alert.sensor_id.in_(sensor_ids)) & 
                        (Alert.acknowledged == False)
                    )
                ).one()
                
                alerts = session.exec(
                    select(Alert)
                    .where(
                        (Alert.sensor_id.in_(sensor_ids)) & 
                        (Alert.acknowledged == False)
                    )
                    .order_by(Alert.timestamp.desc())
                    .limit(5)
                ).all()
            else:
                self.active_alerts = 0
                alerts = []
            
            alerts_display = []
            for a in alerts:
                s = session.get(Sensor, a.sensor_id)
                diff = datetime.now() - a.timestamp
                if diff.total_seconds() < 3600:
                    time_ago = f"{int(diff.total_seconds() / 60)}m atrás"
                elif diff.total_seconds() < 86400:
                    time_ago = f"{int(diff.total_seconds() / 3600)}h atrás"
                else:
                    time_ago = f"{int(diff.days)}d atrás"
                
                alerts_display.append({
                    "id": a.id,
                    "sensor_code": s.id_code if s else "Desconocido",
                    "type": a.type,
                    "message": a.message,
                    "time_ago": time_ago,
                })
            
            self.active_alerts_list = alerts_display

    @rx.event
    async def acknowledge_alert(self, alert_id: int):
        """Marca una alerta como vista"""
        with Session(engine) as session:
            alert = session.get(Alert, alert_id)
            if alert:
                alert.acknowledged = True
                session.add(alert)
                session.commit()
        
        await self.load_dashboard_stats()
        return rx.toast("Alerta confirmada", duration=3000, close_button=True)

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
                await self.load_dashboard_stats()
            await asyncio.sleep(5)

    @rx.event
    def stop_polling(self):
        """Stop background polling"""
        self.is_polling = False

    @rx.var
    def critical_count(self) -> int:
        """Cuenta sensores en estado crítico"""
        return len([s for s in self.sensor_statuses if s.get("status") == "red"])
