# app/services/data_aggregator.py
import json
import logging
import threading
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from sqlmodel import Session

from app.models import Alert, Sensor, SensorData
from app.utils import engine

logger = logging.getLogger(__name__)


class SensorDataAggregator:
    """
    Agregador que acumula lecturas de sensores cada 5 segundos
    y guarda la media aritmética cada 5 minutos
    """
    
    def __init__(self, interval_minutes: int = 5):
        """
        Args:
            interval_minutes: Intervalo en minutos para calcular y guardar la media
        """
        self.interval_seconds = interval_minutes * 60
        self.buffer: Dict[int, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.raw_data_buffer: Dict[int, List[dict]] = defaultdict(list)
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        
        logger.info(f"📊 Agregador inicializado: media cada {interval_minutes} minutos")
    
    def add_reading(self, sensor_id: int, sensor_type: str, data: dict):
        """
        Añade una lectura al buffer para calcular la media posteriormente
        
        Args:
            sensor_id: ID del sensor
            sensor_type: Tipo de dato (temperatura, humedad_ambiente, etc.)
            data: Diccionario con todos los datos del sensor
        """
        with self.lock:
            # Obtener el valor específico del sensor
            value = data.get(sensor_type, 0.0)
            
            # Guardar valor en buffer para calcular media
            self.buffer[sensor_id][sensor_type].append(float(value))
            
            # Guardar también los datos completos (para el campo raw)
            self.raw_data_buffer[sensor_id].append(data)
            
            logger.debug(
                f"📥 Lectura añadida: Sensor {sensor_id} ({sensor_type}) = {value:.2f} "
                f"[{len(self.buffer[sensor_id][sensor_type])} lecturas acumuladas]"
            )
    
    def _calculate_and_save_averages(self):
        """
        Calcula la media aritmética de todas las lecturas acumuladas 
        y las guarda en la base de datos
        """
        with self.lock:
            if not self.buffer:
                logger.debug("📊 No hay lecturas para procesar")
                return
            
            # Copiar y limpiar buffers
            buffer_snapshot = dict(self.buffer)
            raw_data_snapshot = dict(self.raw_data_buffer)
            self.buffer.clear()
            self.raw_data_buffer.clear()
        
        # Procesar fuera del lock para no bloquear nuevas lecturas
        timestamp = datetime.now()
        
        try:
            with Session(engine) as session:
                for sensor_id, types_data in buffer_snapshot.items():
                    for sensor_type, values in types_data.items():
                        if not values:
                            continue
                        
                        # Calcular media aritmética
                        avg_value = sum(values) / len(values)
                        
                        # Crear resumen para el campo raw
                        raw_summary = {
                            'aggregated': True,
                            'interval_minutes': self.interval_seconds // 60,
                            'samples_count': len(values),
                            'min': min(values),
                            'max': max(values),
                            'avg': avg_value,
                            'sensor_type': sensor_type,
                            'timestamp': timestamp.isoformat()
                        }
                        
                        # Añadir datos adicionales del último mensaje completo si existen
                        if sensor_id in raw_data_snapshot and raw_data_snapshot[sensor_id]:
                            last_data = raw_data_snapshot[sensor_id][-1]
                            # Convertir datetime a string si existe
                            if 'timestamp' in last_data and isinstance(last_data['timestamp'], datetime):
                                last_data = last_data.copy()
                                last_data['timestamp'] = last_data['timestamp'].isoformat()
                            raw_summary['last_sample'] = last_data
                        
                        # Guardar en BD
                        reading = SensorData(
                            sensor_id=sensor_id,
                            timestamp=timestamp,
                            value=round(avg_value, 2),
                            raw=json.dumps(raw_summary)
                        )
                        
                        session.add(reading)
                        
                        logger.info(
                            f"💾 Media guardada: Sensor {sensor_id} ({sensor_type}) = {avg_value:.2f} "
                            f"(de {len(values)} lecturas: min={min(values):.2f}, max={max(values):.2f})"
                        )
                        
                        # Verificar umbrales con la media
                        self._check_thresholds(session, sensor_id, sensor_type, avg_value)
                
                session.commit()
                logger.info(f"✅ Guardado completado: {len(buffer_snapshot)} sensores procesados")
                
        except Exception as e:
            logger.exception(f"❌ Error guardando medias: {e}")
    
    def _check_thresholds(self, session: Session, sensor_id: int, sensor_type: str, value: float):
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
                    f"Media: {value:.2f} {sensor.unit} (límite: {sensor.threshold_low})"
                )
            elif value > sensor.threshold_high:
                alert_type = "high"
                alert_message = (
                    f"⚠️ {sensor.id_code}: {sensor_type} sobre el máximo. "
                    f"Media: {value:.2f} {sensor.unit} (límite: {sensor.threshold_high})"
                )
            
            if alert_type and alert_message:
                alert = Alert(
                    sensor_id=sensor_id,
                    timestamp=datetime.now(),
                    type=alert_type,
                    message=alert_message,
                    acknowledged=False
                )
                session.add(alert)
                session.commit()
                logger.warning(f"🚨 ALERTA: {alert_message}")
                
        except Exception as e:
            logger.exception(f"❌ Error verificando umbrales: {e}")
    
    def _aggregation_loop(self):
        """Loop que ejecuta el guardado de medias cada intervalo configurado"""
        logger.info(f"🔄 Loop de agregación iniciado (cada {self.interval_seconds}s)")
        
        while self.running:
            time.sleep(self.interval_seconds)
            
            if self.running:  # Verificar nuevamente después del sleep
                logger.info("⏰ Ejecutando agregación de datos...")
                self._calculate_and_save_averages()
    
    def start(self):
        """Inicia el thread de agregación"""
        if self.running:
            logger.warning("⚠️ El agregador ya está en ejecución")
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._aggregation_loop,
            daemon=True,
            name="DataAggregator-Thread"
        )
        self.thread.start()
        logger.info("✅ Agregador de datos iniciado en background")
    
    def stop(self):
        """Detiene el thread de agregación y guarda datos pendientes"""
        logger.info("🛑 Deteniendo agregador de datos...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        # Guardar datos pendientes
        logger.info("💾 Guardando datos pendientes...")
        self._calculate_and_save_averages()
        logger.info("✅ Agregador detenido correctamente")


# Instancia global del agregador (5 minutos por defecto)
data_aggregator = SensorDataAggregator(interval_minutes=5)
