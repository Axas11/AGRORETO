# app/services/maiota_client.py
import json
import logging
import re
import threading
import time
import uuid
from datetime import datetime
from typing import Callable, Dict

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class MAIoTAMultiSensorClient:
    """Cliente MQTT para gestionar múltiples sensores MAIoTA del Reto Agrotech"""
    
    def __init__(self):
        """
        Inicializa el cliente MQTT para sensores MAIoTA.
        Crea un client_id único y configura los parámetros de conexión.
        """
        # ✅ Client ID único usando UUID
        unique_id = str(uuid.uuid4())[:8]
        self.client_id = f"Equipo3_{unique_id}"
        
        self.broker = "broker.emqx.io"
        self.port = 1883
        self.keepalive = 60
        
        self.topic_callbacks: Dict[str, Callable] = {}
        self.active_sensors: Dict[str, dict] = {}
        
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """
        Inicializa el cliente MQTT con configuración optimizada.
        Configura callbacks y reconexion automática.
        """
        self.client = mqtt.Client(
            client_id=self.client_id,
            clean_session=True,  # ✅ Limpiar sesión anterior
            protocol=mqtt.MQTTv311
        )
        
        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # ✅ Configuración de reconexión automática
        self.client.reconnect_delay_set(min_delay=1, max_delay=120)
        
        logger.info(f"🆔 Cliente MQTT inicializado: {self.client_id}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback ejecutado cuando se conecta exitosamente al broker MQTT.
        Re-suscribe automáticamente a todos los topics registrados.
        
        Args:
            client: Instancia del cliente MQTT
            userdata: Datos de usuario (no usado)
            flags: Flags de conexión
            rc: Código de resultado (0 = éxito)
        """
        if rc == 0:
            logger.info("✅ Conectado al broker MAIoTA (EMQX)")
            self.is_connected = True
            self.reconnect_attempts = 0
            
            # Resuscribirse a todos los topics
            for topic in self.topic_callbacks.keys():
                client.subscribe(topic)
                logger.info(f"  📡 Suscrito a: {topic}")
        else:
            error_messages = {
                1: "Versión de protocolo incorrecta",
                2: "Identificador de cliente rechazado",
                3: "Servidor no disponible",
                4: "Usuario/contraseña incorrectos",
                5: "No autorizado (client_id duplicado)",
            }
            error = error_messages.get(rc, f"Error desconocido: {rc}")
            logger.error(f"❌ Error de conexión MQTT: {error}")
            self.is_connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Callback ejecutado cuando se desconecta del broker MQTT.
        Intenta reconectar automáticamente si fue desconexión inesperada.
        
        Args:
            client: Instancia del cliente MQTT
            userdata: Datos de usuario (no usado)
            rc: Código de resultado (0 = desconexión limpia)
        """
        self.is_connected = False
        
        if rc != 0:
            logger.warning(f"⚠️ Desconexión inesperada del broker (código: {rc})")
            self.reconnect_attempts += 1
            
            if self.reconnect_attempts < self.max_reconnect_attempts:
                logger.info(f"🔄 Intentando reconectar... (intento {self.reconnect_attempts}/{self.max_reconnect_attempts})")
            else:
                logger.error("❌ Máximo de intentos de reconexión alcanzado")
        else:
            logger.info("👋 Desconectado del broker MAIoTA")
    
    def _on_message(self, client, userdata, msg):
        """
        Procesa mensajes MQTT recibidos de los sensores MAIoTA.
        Parsea el payload y ejecuta el callback correspondiente al topic.
        
        Args:
            client: Instancia del cliente MQTT
            userdata: Datos de usuario (no usado)
            msg: Mensaje MQTT con topic y payload
        """
        topic = msg.topic
        payload = str(msg.payload.decode("utf-8"))
        
        logger.debug(f"📨 Mensaje recibido [{topic}]: {payload[:50]}...")
        
        # Parsear payload MAIoTA
        sensor_data = self._parse_maiota_payload(payload)
        
        if sensor_data and topic in self.topic_callbacks:
            sensor_info = self.active_sensors.get(topic, {})
            sensor_data.update({
                'sensor_code': sensor_info.get('code', 'Unknown'),
                'sensor_id': sensor_info.get('id'),
                'sensor_type': sensor_info.get('type', 'temperatura'),
                'topic': topic,
                'raw_payload': payload
            })
            
            # Ejecutar callback
            try:
                self.topic_callbacks[topic](sensor_data)
            except Exception as e:
                logger.exception(f"❌ Error en callback para {topic}: {e}")
    
    def _parse_maiota_payload(self, payload: str) -> dict:
        """
        Parsea el formato de datos MAIoTA y convierte a diccionario.
        
        Formato esperado: CIoTA-D1=2603&D2=5411&D3=2542&D4=43&D5=580&D6=103&D7=1&
        
        Mapeo de datos:
        - D1 = Temperatura (°C, dividir entre 100)
        - D2 = Humedad Ambiente (%, dividir entre 100)
        - D3 = Humedad Suelo (%, dividir entre 100)
        - D4 = Iluminación (Lux, dividir entre 10)
        - D5 = CO2 (ppm, valor directo)
        - D6 = COV (Index, valor directo)
        - D7 = NOx (Index, valor directo)
        
        Args:
            payload: String con el mensaje MQTT en formato MAIoTA
        
        Returns:
            Diccionario con los datos parseados o None si el formato es inválido
        """
        if not payload.startswith("CIoTA-"):
            logger.warning(f"⚠️ Payload no reconocido: {payload}")
            return None
        
        pattern = r'D(\d+)=([↓]?)(\d+)'
        matches = re.findall(pattern, payload)
        
        raw_values = {}
        for match in matches:
            data_num = int(match[0])
            arrow = match[1]  # ↓ indica valor por debajo del mínimo
            value = int(match[2])
            raw_values[f'D{data_num}'] = (value, arrow)
        
        return {
            'timestamp': datetime.now(),
            'temperatura': raw_values.get('D1', (0, ''))[0] / 100,
            'humedad_ambiente': raw_values.get('D2', (0, ''))[0] / 100,
            'humedad_suelo': raw_values.get('D3', (0, ''))[0] / 100,
            'iluminacion': raw_values.get('D4', (0, ''))[0] / 10,
            'co2': raw_values.get('D5', (0, ''))[0],
            'cov': raw_values.get('D6', (0, ''))[0],
            'nox': raw_values.get('D7', (0, ''))[0],
            'humedad_suelo_baja': raw_values.get('D3', (0, ''))[1] == '↓'
        }
    
    def add_sensor(self, sensor_id: int, sensor_code: str, sensor_type: str, 
                   topic: str, callback: Callable):
        """
        Registra un nuevo sensor en el cliente MQTT y se suscribe a su topic.
        
        Args:
            sensor_id: ID del sensor en la base de datos
            sensor_code: Código identificador del sensor (ej: M-TEMP-01)
            sensor_type: Tipo de sensor (temperatura, humedad, etc.)
            topic: Topic MQTT del cual recibir datos
            callback: Función a ejecutar cuando lleguen datos del sensor
        """
        self.active_sensors[topic] = {
            'id': sensor_id,
            'code': sensor_code,
            'type': sensor_type
        }
        self.topic_callbacks[topic] = callback
        
        if self.is_connected:
            self.client.subscribe(topic)
            logger.info(f"✅ Sensor {sensor_code} ({sensor_type}) registrado en topic {topic}")
        else:
            logger.warning(f"⏳ Sensor {sensor_code} pendiente de conexión")
    
    def remove_sensor(self, topic: str):
        """
        Elimina un sensor del monitoreo y cancela la suscripción al topic.
        
        Args:
            topic: Topic MQTT del sensor a eliminar
        """
        if topic in self.topic_callbacks:
            sensor_info = self.active_sensors.get(topic, {})
            del self.topic_callbacks[topic]
            del self.active_sensors[topic]
            
            if self.is_connected:
                self.client.unsubscribe(topic)
                logger.info(f"✅ Sensor {sensor_info.get('code')} desvinculado del topic {topic}")
    
    def start(self):
        """
        Inicia la conexión MQTT en un thread de background.
        El cliente se ejecuta de forma asíncrona sin bloquear la aplicación.
        """
        try:
            logger.info(f"🔌 Conectando a {self.broker}:{self.port}...")
            logger.info(f"🆔 Client ID: {self.client_id}")
            
            # ✅ Conectar con timeout
            self.client.connect(
                self.broker,
                self.port,
                keepalive=self.keepalive
            )
            
            # Ejecutar loop en thread separado
            thread = threading.Thread(
                target=self.client.loop_forever,
                daemon=True,
                name="MAIoTA-MQTT-Thread"
            )
            thread.start()
            logger.info("✅ Cliente MAIoTA ejecutándose en background")
            
        except Exception as e:
            logger.exception(f"❌ Error al iniciar cliente MQTT: {e}")
    
    def stop(self):
        """
        Detiene el cliente MQTT de forma limpia.
        Cierra la conexión y termina el loop del cliente.
        """
        logger.info("🛑 Deteniendo cliente MAIoTA...")
        self.client.loop_stop()
        self.client.disconnect()


# Instancia global del cliente
maiota_client = MAIoTAMultiSensorClient()
