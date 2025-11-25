#app/services/maiota_client.py
import paho.mqtt.client as mqtt
import threading
from datetime import datetime
import re
import json
import logging
from typing import Dict, Callable

logger = logging.getLogger(__name__)

class MAIoTAMultiSensorClient:
    """Cliente MQTT para gestionar múltiples sensores MAIoTA del Reto Agrotech"""
    
    def __init__(self):
        self.client_id = "Equipo 3"
        self.broker = "broker.emqx.io"
        self.port = 1883
        
        self.topic_callbacks: Dict[str, Callable] = {}
        self.active_sensors: Dict[str, dict] = {}
        
        self.is_connected = False
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Inicializa el cliente MQTT"""
        self.client = mqtt.Client(self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ Conectado al broker MAIoTA (EMQX)")
            self.is_connected = True
            
            # Resuscribirse a todos los topics
            for topic in self.topic_callbacks.keys():
                client.subscribe(topic)
                logger.info(f"  📡 Suscrito a: {topic}")
        else:
            logger.error(f"❌ Error de conexión MQTT: código {rc}")
            self.is_connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        logger.warning("⚠️ Desconectado del broker MAIoTA")
        self.is_connected = False
    
    def _on_message(self, client, userdata, msg):
        """Procesa mensajes MQTT del sensor"""
        topic = msg.topic
        payload = str(msg.payload.decode("utf-8"))
        
        logger.info(f"📨 Mensaje recibido [{topic}]: {payload[:50]}...")
        
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
                logger.exception(f"Error en callback para {topic}: {e}")
    
    def _parse_maiota_payload(self, payload: str) -> dict:
        """
        Parsea el formato MAIoTA:
        CIoTA-D1=2603&D2=5411&D3=2542&D4=43&D5=580&D6=103&D7=1&
        
        D1 = Temperatura (dividir entre 100)
        D2 = Humedad Ambiente (dividir entre 100)
        D3 = Humedad Suelo (dividir entre 100)
        D4 = Iluminación (dividir entre 10)
        D5 = CO2 (directo)
        D6 = COV (directo)
        D7 = NOx (directo)
        """
        if not payload.startswith("CIoTA-"):
            logger.warning(f"Payload no reconocido: {payload}")
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
            'timestamp': datetime.utcnow(),
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
        """Registra un nuevo sensor en el cliente MQTT"""
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
        """Elimina un sensor del monitoreo"""
        if topic in self.topic_callbacks:
            sensor_info = self.active_sensors.get(topic, {})
            del self.topic_callbacks[topic]
            del self.active_sensors[topic]
            
            if self.is_connected:
                self.client.unsubscribe(topic)
                logger.info(f"✅ Sensor {sensor_info.get('code')} desvinculado del topic {topic}")
    
    def start(self):
        """Inicia la conexión MQTT en background"""
        try:
            logger.info(f"🔌 Conectando a {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            
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
        """Detiene el cliente MQTT"""
        logger.info("🛑 Deteniendo cliente MAIoTA...")
        self.client.loop_stop()
        self.client.disconnect()

# Instancia global del cliente
maiota_client = MAIoTAMultiSensorClient()
