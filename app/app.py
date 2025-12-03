# app/app.py
import json
import logging
from datetime import datetime

import reflex as rx
from sqlmodel import Session, select

from app.api.routes import router as api_router
from app.models import Alert, Sensor, SensorData
from app.pages.alerts import alerts_page
from app.pages.dashboard import dashboard
from app.pages.login_form import login_form
from app.pages.parcel_detail import parcel_detail_page
from app.pages.parcels import parcels_page
from app.pages.register_form import register_form
from app.pages.sensor_detail import sensor_detail_page
# Importar MQTT y modelos
from app.services.maiota_client import maiota_client
from app.states.alert_state import AlertState
from app.states.auth_state import AuthState
from app.states.dashboard_state import DashboardState
from app.states.parcel_state import ParcelState
from app.states.sensor_history_state import SensorHistoryState
from app.states.sensor_state import SensorState
from app.utils import engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_sensor_reading_direct(sensor_id: int, sensor_type: str, data: dict):
    """Guarda lectura directamente en BD sin usar State"""
    try:
        with Session(engine) as session:
            # Extraer valor según tipo de sensor
            value = data.get(sensor_type, 0.0)
            
            # Convertir datetime a string para JSON
            data_for_json = data.copy()
            if 'timestamp' in data_for_json and isinstance(data_for_json['timestamp'], datetime):
                data_for_json['timestamp'] = data_for_json['timestamp'].isoformat()
            
            # Crear registro
            reading = SensorData(
                sensor_id=sensor_id,
                timestamp=data.get('timestamp', datetime.utcnow()),
                value=float(value),
                raw=data.get('raw_payload', json.dumps(data_for_json))
            )
            
            session.add(reading)
            session.commit()
            
            logger.info(f"💾 Lectura guardada: Sensor {sensor_id} ({sensor_type}) = {value:.2f}")
            
            # Verificar umbrales
            check_thresholds_direct(session, sensor_id, sensor_type, value)
            
    except Exception as e:
        logger.exception(f"❌ Error guardando lectura: {e}")


def check_thresholds_direct(session: Session, sensor_id: int, sensor_type: str, value: float):
    """Verifica umbrales y crea alertas si es necesario"""
    try:
        sensor = session.get(Sensor, sensor_id)
        if not sensor:
            return
        
        alert_type = None
        alert_message = None
        
        if value < sensor.threshold_low:
            alert_type = "low"
            alert_message = (
                f"⚠️ {sensor.id_code}: {sensor_type} bajo el mínimo. "
                f"Valor: {value:.2f} {sensor.unit} (límite: {sensor.threshold_low})"
            )
        elif value > sensor.threshold_high:
            alert_type = "high"
            alert_message = (
                f"⚠️ {sensor.id_code}: {sensor_type} sobre el máximo. "
                f"Valor: {value:.2f} {sensor.unit} (límite: {sensor.threshold_high})"
            )
        
        if alert_type and alert_message:
            alert = Alert(
                sensor_id=sensor_id,
                timestamp=datetime.utcnow(),
                type=alert_type,
                message=alert_message,
                acknowledged=False
            )
            session.add(alert)
            session.commit()
            logger.warning(f"🚨 ALERTA: {alert_message}")
            
    except Exception as e:
        logger.exception(f"❌ Error verificando umbrales: {e}")


def load_existing_sensors():
    """Carga sensores existentes y los agrupa por topic"""
    try:
        with Session(engine) as session:
            active_sensors = session.exec(
                select(Sensor).where(Sensor.active == True)
            ).all()
            
            # Agrupar sensores por topic
            sensors_by_topic = {}
            for sensor in active_sensors:
                topic = sensor.mqtt_topic
                if topic not in sensors_by_topic:
                    sensors_by_topic[topic] = []
                sensors_by_topic[topic].append({
                    'id': sensor.id,
                    'code': sensor.id_code,
                    'type': sensor.type,
                })
            
            # Mapeo de tipos
            type_map = {
                "temperature": "temperatura",
                "humidity_ambient": "humedad_ambiente",
                "humidity_soil": "humedad_suelo",
                "luminosity": "iluminacion",
                "co2": "co2",
                "cov": "cov",
                "nox": "nox"
            }
            
            # Registrar un callback POR TOPIC que guarda en TODOS los sensores
            for topic, sensors_list in sensors_by_topic.items():
                
                def make_callback_for_topic(topic_sensors):
                    def on_data(data: dict):
                        """
                        Callback que guarda datos en TODOS los sensores del topic
                        """
                        for sensor_info in topic_sensors:
                            s_id = sensor_info['id']
                            s_type = sensor_info['type']
                            s_code = sensor_info['code']
                            
                            # Mapear tipo de BD a tipo MAIoTA
                            maiota_type = type_map.get(s_type, s_type)
                            
                            try:
                                save_sensor_reading_direct(s_id, maiota_type, data)
                            except Exception as e:
                                logger.exception(f"❌ Error procesando {s_code}: {e}")
                    
                    return on_data
                
                # Registrar el callback para este topic
                # Usar el primer sensor como referencia
                first_sensor = sensors_list[0]
                maiota_client.add_sensor(
                    sensor_id=first_sensor['id'],
                    sensor_code=f"Topic_{topic[:20]}",
                    sensor_type=type_map.get(first_sensor['type'], 'temperatura'),
                    topic=topic,
                    callback=make_callback_for_topic(sensors_list)
                )
                
                logger.info(f"✅ Topic {topic} con {len(sensors_list)} sensores registrados")
            
            total_sensors = sum(len(sensors) for sensors in sensors_by_topic.values())
            logger.info(f"✅ Total: {total_sensors} sensores en {len(sensors_by_topic)} topics")
    
    except Exception as e:
        logger.exception(f"❌ Error cargando sensores existentes: {e}")


#definir registro
def register_page() -> rx.Component:
    return register_form()

def login_page() -> rx.Component:
    return login_form()


def dashboard_page() -> rx.Component:
    return dashboard()


def index() -> rx.Component:
    """Redirect root to dashboard (which will redirect to login if needed)."""
    return rx.el.div(rx.script("window.location.href = '/login'"))

def api_routes(api_app):
    """Registra las rutas de la API REST"""
    from fastapi import FastAPI

    # Crear app FastAPI temporal
    fastapi_app = FastAPI()
    fastapi_app.include_router(api_router)
    
    # Montar en Starlette
    api_app.mount("/api", fastapi_app)
    return api_app

# ==================== INICIALIZACIÓN MQTT ====================
logger.info("🚀 Iniciando aplicación Agrotech...")
logger.info("🔌 Conectando al cliente MQTT MAIoTA...")

# Iniciar cliente MQTT
maiota_client.start()

# Esperar conexión
import time

time.sleep(2)

# Cargar sensores existentes
logger.info("📡 Cargando sensores existentes...")
load_existing_sensors()

logger.info("✅ Sistema de monitoreo MAIoTA iniciado")
# =============================================================


app = rx.App(
    theme=rx.theme(appearance="light"),
    api_transformer=api_routes,
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
    
)

app.add_page(
    login_page,
    route="/login",
    title="Login - Agrotech",
    on_load=AuthState.ensure_db_seeded,
)

app.add_page(
    login_page,
    route="/",  
    title="Login - Agrotech",
    on_load=AuthState.ensure_db_seeded,
)

#registro pagina
app.add_page(
    register_page,
    route="/register",
    title="Register - Agrotech",
    on_load=AuthState.ensure_db_seeded,
)

app.add_page(
    dashboard_page,
    route="/dashboard",
    title="Dashboard - Agrotech",
    on_load=[
        AuthState.check_authentication,
        AuthState.ensure_db_seeded,
        DashboardState.load_dashboard_stats,
        DashboardState.start_polling,
    ],
)
app.add_page(
    parcels_page,
    route="/parcels",
    title="Parcels - Agrotech",
    on_load=[AuthState.check_authentication,
             AuthState.ensure_db_seeded,
               ParcelState.load_parcels],
)
app.add_page(
    parcel_detail_page,
    route="/parcels/[id]",
    title="Parcel Detail - Agrotech",
    on_load=[AuthState.check_authentication,
             AuthState.ensure_db_seeded,
               SensorState.load_sensors],
)
app.add_page(
    sensor_detail_page,
    route="/sensors/[id]",
    title="Sensor Analysis - Agrotech",
    on_load=[AuthState.check_authentication,
             AuthState.ensure_db_seeded, 
             SensorHistoryState.load_history],
)
app.add_page(
    alerts_page,
    route="/alerts",
    title="Alerts - Agrotech",
    on_load=[AuthState.check_authentication,
             AuthState.ensure_db_seeded, 
             AlertState.load_alerts],
)
