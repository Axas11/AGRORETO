# app/states/alert_state.py
import reflex as rx
from sqlmodel import Session, desc, select

from app.models import Alert, Parcel, ParcelTechnician, Sensor
from app.states.auth_state import AuthState
from app.utils import engine


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
    async def load_alerts(self):
        """Carga alertas según permisos del usuario"""
        # ✅ Obtener info del usuario
        auth_state = await self.get_state(AuthState)
        user_role = auth_state.user_role
        user_id = auth_state.user_id
        
        if not user_id:
            self.alerts = []
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
                self.alerts = []
                return
            
            # ✅ Obtener sensores de parcelas accesibles
            accessible_sensors = session.exec(
                select(Sensor).where(Sensor.parcel_id.in_(parcel_ids))
            ).all()
            
            sensor_ids = [s.id for s in accessible_sensors]
            
            if not sensor_ids:
                self.alerts = []
                return
            
            # ✅ Consulta de alertas filtradas por sensores accesibles
            query = select(Alert).where(Alert.sensor_id.in_(sensor_ids))
            
            if not self.show_history:
                query = query.where(Alert.acknowledged == False)
            
            if self.filter_type != "all":
                query = query.where(Alert.type == self.filter_type)
            
            query = query.order_by(desc(Alert.timestamp))
            results = session.exec(query).all()
            
            display_list = []
            for a in results:
                s = session.get(Sensor, a.sensor_id)
                display_list.append({
                    "id": a.id,
                    "sensor_code": s.id_code if s else "Desconocido",
                    "sensor_type": s.type if s else "",
                    "type": a.type,
                    "message": a.message,
                    "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "acknowledged": a.acknowledged,
                    "color": "red" if a.type == "HIGH" else "amber",
                })
            
            self.alerts = display_list

    @rx.event
    async def acknowledge_alert(self, alert_id: int):
        """Marca una alerta como vista"""
        with Session(engine) as session:
            alert = session.get(Alert, alert_id)
            if alert:
                alert.acknowledged = True
                session.add(alert)
                session.commit()
        
        await self.load_alerts()
        return rx.toast("Alerta confirmada", duration=3000, close_button=True)

    @rx.event
    async def acknowledge_all_alerts(self):
        """Marca todas las alertas visibles como reconocidas"""
        auth_state = await self.get_state(AuthState)
        user_role = auth_state.user_role
        user_id = auth_state.user_id
        
        if not user_id:
            return
        
        with Session(engine) as session:
            # ✅ Determinar sensores accesibles
            if user_role == "farmer":
                accessible_parcels = session.exec(select(Parcel)).all()
            else:
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
            accessible_sensors = session.exec(
                select(Sensor).where(Sensor.parcel_id.in_(parcel_ids))
            ).all()
            sensor_ids = [s.id for s in accessible_sensors]
            
            # ✅ Actualizar solo alertas de sensores accesibles
            query = select(Alert).where(
                (Alert.sensor_id.in_(sensor_ids)) & 
                (Alert.acknowledged == False)
            )
            
            if self.filter_type != "all":
                query = query.where(Alert.type == self.filter_type)
            
            alerts_to_ack = session.exec(query).all()
            count = len(alerts_to_ack)
            
            for alert in alerts_to_ack:
                alert.acknowledged = True
                session.add(alert)
            
            session.commit()
        
        await self.load_alerts()
        return rx.toast(f"{count} alerta(s) confirmada(s)", duration=3000, close_button=True)
