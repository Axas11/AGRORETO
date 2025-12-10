# app/states/sensor_state.py
import json
import logging
from datetime import datetime

import reflex as rx
from sqlmodel import Session, select

from app.models import Alert, Parcel, ParcelTechnician, Sensor, SensorData
from app.services.maiota_client import maiota_client
from app.states.auth_state import AuthState
from app.utils import engine


class SensorState(rx.State):
    sensors: list[dict] = []
    current_parcel: Parcel | None = None
    show_add_sensor_modal: bool = False
    
    # Campos del formulario (existentes)
    new_sensor_code: str = ""
    new_sensor_type: str = "temperature"
    new_sensor_unit: str = "°C"
    new_sensor_desc: str = ""
    new_sensor_low: float = 0.0
    new_sensor_high: float = 100.0
    
    # Nuevo campo para MQTT
    new_sensor_mqtt_topic: str = "Awi7LJfyyn6LPjg/15046220"
    
    # Mapeo de tipos de sensor MAIoTA
    maiota_type_map = {
        "temperature": "temperatura",
        "humidity_ambient": "humedad_ambiente",
        "humidity_soil": "humedad_suelo",
        "luminosity": "iluminacion",
        "co2": "co2",
        "cov": "cov",
        "nox": "nox"
    }

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
    async def load_sensors(self):
        """Carga sensores de la parcela actual"""
        self.sensors = []
        self.current_parcel = None
        pid = self.parcel_id
        if not pid:
            return
        
        # ✅ Obtener el estado de autenticación correctamente
        auth_state = await self.get_state(AuthState)
        user_role = auth_state.user_role
        user_id = auth_state.user_id
        
        with Session(engine) as session:
            # Verificar permisos: sólo farmer, owner o técnicos asignados pueden ver detalles
            parcel_obj = session.get(Parcel, pid)
            if not parcel_obj:
                return

            allowed = False
            if user_role == "farmer":
                allowed = True
            elif parcel_obj.owner_id == user_id:
                allowed = True
            else:
                # Comprobar asignación en ParcelTechnician
                assigned = session.exec(
                    select(ParcelTechnician).where(
                        (ParcelTechnician.parcel_id == pid) & (ParcelTechnician.user_id == user_id)
                    )
                ).first()
                if assigned:
                    allowed = True

            if not allowed:
                # No autorizado para ver esta parcela
                return

            self.current_parcel = parcel_obj
            if self.current_parcel:
                sensors_objs = session.exec(
                    select(Sensor).where(Sensor.parcel_id == pid)
                ).all()
                self.sensors = [s.model_dump() for s in sensors_objs]


    @rx.event
    def toggle_add_modal(self):
        self.show_add_sensor_modal = not self.show_add_sensor_modal
        if not self.show_add_sensor_modal:
            self._reset_form()

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
        elif val == "co2":
            self.new_sensor_unit = "ppm"
        elif val in ["cov", "nox"]:
            self.new_sensor_unit = "Index"

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
    def set_sensor_mqtt_topic(self, val: str):
        """Nuevo método para configurar el topic MQTT"""
        self.new_sensor_mqtt_topic = val

    @rx.event
    def add_sensor(self):
        """Crea sensor y lo registra en MQTT"""
        if not self.current_parcel:
            logging.error("No hay parcela seleccionada")
            return
        
        try:
            with Session(engine) as session:
                new_sensor = Sensor(
                    id_code=self.new_sensor_code,
                    parcel_id=self.current_parcel.id,
                    type=self.new_sensor_type,
                    unit=self.new_sensor_unit,
                    description=self.new_sensor_desc,
                    threshold_low=self.new_sensor_low,
                    threshold_high=self.new_sensor_high,
                    mqtt_topic=self.new_sensor_mqtt_topic,  # Nuevo campo
                    active=True
                )
                session.add(new_sensor)
                session.commit()
                session.refresh(new_sensor)
                
                # Registrar en MQTT
                self._register_sensor_mqtt(new_sensor)
                
                logging.info(f"✓ Sensor {new_sensor.id_code} creado con ID {new_sensor.id}")
        
        except Exception as e:
            logging.exception(f"Error creando sensor: {e}")
        
        self.toggle_add_modal()
        self.load_sensors()

    def _reset_form(self):
        """Limpia el formulario"""
        self.new_sensor_code = ""
        self.new_sensor_type = "temperature"
        self.new_sensor_unit = "°C"
        self.new_sensor_desc = ""
        self.new_sensor_low = 0.0
        self.new_sensor_high = 100.0
        self.new_sensor_mqtt_topic = "Awi7LJfyyn6LPjg/15046220"

    def _register_sensor_mqtt(self, sensor: Sensor):
        """Registra el sensor en el cliente MQTT"""
        
        # Obtener el tipo MAIoTA correspondiente
        maiota_type = self.maiota_type_map.get(sensor.type, "temperatura")
        
        def on_sensor_data(data: dict):
            """Callback cuando llegan datos del sensor"""
            self._save_sensor_reading(sensor.id, maiota_type, data)
            self._check_thresholds(sensor, maiota_type, data)
        
        maiota_client.add_sensor(
            sensor_id=sensor.id,
            sensor_code=sensor.id_code,
            sensor_type=maiota_type,
            topic=sensor.mqtt_topic,
            callback=on_sensor_data
        )
        
        logging.info(f"✓ Sensor {sensor.id_code} registrado en MQTT topic {sensor.mqtt_topic}")

    def _save_sensor_reading(self, sensor_id: int, sensor_type: str, data: dict):
        """Guarda lectura en la base de datos"""
        try:
            with Session(engine) as session:
                # Extraer valor según el tipo de sensor
                value = data.get(sensor_type, 0.0)
                
                # Convertir datetime a string para JSON
                data_for_json = data.copy()
                if 'timestamp' in data_for_json:
                    if isinstance(data_for_json['timestamp'], datetime):
                        data_for_json['timestamp'] = data_for_json['timestamp'].isoformat()
                
                reading = SensorData(
                    sensor_id=sensor_id,
                    timestamp=data.get('timestamp', datetime.now()),
                    value=float(value),
                    raw=data.get('raw_payload', json.dumps(data_for_json))  # ← Usa data_for_json
                )
                
                session.add(reading)
                session.commit()
                
                logging.debug(f"💾 Lectura guardada: Sensor {sensor_id} = {value}")
                
        except Exception as e:
            logging.exception(f"Error guardando lectura: {e}")
    #Comentada por duplicado de mensaje

    # def _check_thresholds(self, sensor: Sensor, sensor_type: str, data: dict):
    #     """Verifica umbrales y crea alertas si es necesario"""
    #     value = data.get(sensor_type, 0.0)
        
    #     alert_type = None
    #     alert_message = None
        
    #     if value < sensor.threshold_low:
    #         alert_type = "low"
    #         alert_message = (
    #             f"⚠️ {sensor.id_code}: {sensor_type} bajo el mínimo. "
    #             f"Valor: {value:.2f} {sensor.unit} (límite: {sensor.threshold_low})"
    #         )
    #     elif value > sensor.threshold_high:
    #         alert_type = "high"
    #         alert_message = (
    #             f"⚠️ {sensor.id_code}: {sensor_type} sobre el máximo. "
    #             f"Valor: {value:.2f} {sensor.unit} (límite: {sensor.threshold_high})"
    #         )
        
    #     if alert_type and alert_message:
    #         self._create_alert(sensor.id, alert_type, alert_message)
            

    def _create_alert(self, sensor_id: int, alert_type: str, message: str):
        """Crea una alerta en la base de datos"""
        try:
            with Session(engine) as session:
                alert = Alert(
                    sensor_id=sensor_id,
                    timestamp=datetime.now(),
                    type=alert_type,
                    message=message,
                    acknowledged=False
                )
                
                session.add(alert)
                session.commit()
                
                logging.warning(f"🚨 ALERTA: {message}")
                
        except Exception as e:
            logging.exception(f"Error creando alerta: {e}")

    @rx.event
    def delete_sensor(self, sensor_id: int):
        """Elimina sensor y lo desregistra del MQTT"""
        try:
            with Session(engine) as session:
                sensor = session.get(Sensor, sensor_id)
                if sensor:
                    # Desregistrar de MQTT antes de eliminar
                    maiota_client.remove_sensor(sensor.mqtt_topic)
                    logging.info(f"✓ Sensor {sensor.id_code} desvinculado de MQTT")
                    
                    session.delete(sensor)
                    session.commit()
            
            self.load_sensors()
            
        except Exception as e:
            logging.exception(f"Error eliminando sensor: {e}")
