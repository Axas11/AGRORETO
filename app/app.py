# app/app.py
import logging
import time

import reflex as rx
from sqlmodel import Session, select

from app.api.routes import router as api_router
from app.models import Sensor
from app.pages.admin_users import AdminUserState, admin_users_page
from app.pages.alerts import alerts_page
from app.pages.dashboard import dashboard
from app.pages.index import index
from app.pages.info import info
from app.pages.login_form import login_form
from app.pages.parcel_detail import parcel_detail_page
from app.pages.parcels import parcels_page
from app.pages.register_form import register_form
from app.pages.sensor_detail import sensor_detail_page
# Importar MQTT y modelos
from app.services.maiota_client import maiota_client
from app.services.data_aggregator import data_aggregator
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
    """
    Añade una lectura de sensor al agregador para calcular medias cada 5 minutos.
    No guarda directamente en la base de datos, acumula en memoria.
    
    Args:
        sensor_id: ID del sensor en la base de datos
        sensor_type: Tipo de dato (temperatura, humedad_ambiente, etc.)
        data: Diccionario con los datos del sensor recibidos por MQTT
    """
    try:
        # En lugar de guardar directamente, añadir al buffer del agregador
        data_aggregator.add_reading(sensor_id, sensor_type, data)
        
        # Log reducido para no saturar
        logger.debug(f"📥 Lectura añadida al buffer: Sensor {sensor_id} ({sensor_type})")
            
    except Exception as e:
        logger.exception(f"❌ Error añadiendo lectura al agregador: {e}")


def check_thresholds_direct(session: Session, sensor_id: int, sensor_type: str, value: float):
    """
    FUNCIÓN DEPRECADA: Los umbrales ahora se verifican en el agregador con las medias.
    La verificación de umbrales se realiza en data_aggregator._check_thresholds().
    Se mantiene por compatibilidad pero no se usa.
    """
    pass


def load_existing_sensors():
    """
    Carga todos los sensores activos de la BD y los registra en el cliente MQTT.
    Agrupa sensores por topic MQTT para optimizar las suscripciones.
    Cada topic puede tener múltiples sensores que reciben los mismos datos.
    """
    try:
        with Session(engine) as session:
            active_sensors = session.exec(
                select(Sensor).where(Sensor.active.is_(True))
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
                    """
                    Crea una función callback para un topic MQTT específico.
                    El callback procesa datos para todos los sensores asociados al topic.
                    
                    Args:
                        topic_sensors: Lista de sensores que comparten el mismo topic MQTT
                    
                    Returns:
                        Función callback que procesa mensajes MQTT
                    """
                    def on_data(data: dict):
                        """
                        Callback ejecutado cuando llegan datos MQTT del topic.
                        Distribuye los datos a todos los sensores del topic.
                        
                        Args:
                            data: Diccionario con los datos parseados del mensaje MQTT
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
    """Renderiza la página de registro de nuevos usuarios"""
    return register_form()

def login_page() -> rx.Component:
    """Renderiza la página de inicio de sesión"""
    return login_form()

def info_page() -> rx.components:
    """Renderiza la página de información sobre el sistema"""
    return info()

def dashboard_page() -> rx.Component:
    """Renderiza el dashboard principal con estadísticas y gráficos"""
    return dashboard()

def index_page() -> rx.Component:
    """Renderiza la página de inicio/landing page"""
    return index()

def admin_page() -> rx.Component:
    """Renderiza la página de administración de usuarios (solo admin)"""
    return admin_users_page()

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

# Iniciar agregador de datos
logger.info("📊 Iniciando agregador de datos (media cada 5 minutos)...")
data_aggregator.start()

# Esperar conexión
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
    index_page,
    route="/",  
    title="Inicio - Agrotech",
)

app.add_page(
    info_page,
    route="/info",  
    title="Inicio - Agrotech",
    on_load=AuthState.check_auth_or_index,
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
                             SensorState.load_sensors,
                             ParcelState.load_assigned_techs],
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

app.add_page(
    admin_page,
    route="/admin/users",
    title="Admin - Gestión de Usuarios",
    on_load=[AuthState.check_authentication,
             AuthState.ensure_db_seeded, 
             AdminUserState.load_users],
)
