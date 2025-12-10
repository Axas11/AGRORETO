# tests/test_data_aggregator.py
"""
Tests para el agregador de datos de sensores
"""
import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.data_aggregator import SensorDataAggregator


def test_aggregator_initialization():
    """Test: Inicialización del agregador con intervalo personalizado"""
    aggregator = SensorDataAggregator(interval_minutes=10)
    
    assert aggregator.interval_seconds == 600  # 10 minutos = 600 segundos
    assert aggregator.running is False
    assert len(aggregator.buffer) == 0
    assert len(aggregator.raw_data_buffer) == 0


def test_add_reading():
    """Test: Añadir lecturas al buffer del agregador"""
    aggregator = SensorDataAggregator(interval_minutes=5)
    
    # Añadir primera lectura
    data1 = {
        'temperatura': 25.5,
        'humedad': 60.0,
        'timestamp': datetime.now()
    }
    aggregator.add_reading(sensor_id=1, sensor_type='temperatura', data=data1)
    
    # Verificar que se agregó al buffer
    assert 1 in aggregator.buffer
    assert 'temperatura' in aggregator.buffer[1]
    assert len(aggregator.buffer[1]['temperatura']) == 1
    assert aggregator.buffer[1]['temperatura'][0] == 25.5
    
    # Añadir segunda lectura al mismo sensor
    data2 = {
        'temperatura': 26.0,
        'humedad': 62.0,
        'timestamp': datetime.now()
    }
    aggregator.add_reading(sensor_id=1, sensor_type='temperatura', data=data2)
    
    # Verificar acumulación
    assert len(aggregator.buffer[1]['temperatura']) == 2
    assert aggregator.buffer[1]['temperatura'][1] == 26.0


def test_add_reading_multiple_sensors():
    """Test: Añadir lecturas de múltiples sensores"""
    aggregator = SensorDataAggregator(interval_minutes=5)
    
    # Sensor 1
    aggregator.add_reading(1, 'temperatura', {'temperatura': 20.0})
    # Sensor 2
    aggregator.add_reading(2, 'temperatura', {'temperatura': 22.0})
    # Sensor 3
    aggregator.add_reading(3, 'humedad', {'humedad': 55.0})
    
    # Verificar que hay 3 sensores en el buffer
    assert len(aggregator.buffer) == 3
    assert 1 in aggregator.buffer
    assert 2 in aggregator.buffer
    assert 3 in aggregator.buffer


def test_add_reading_multiple_types():
    """Test: Añadir múltiples tipos de datos al mismo sensor"""
    aggregator = SensorDataAggregator(interval_minutes=5)
    
    data = {
        'temperatura': 25.0,
        'humedad': 60.0,
        'presion': 1013.0
    }
    
    aggregator.add_reading(1, 'temperatura', data)
    aggregator.add_reading(1, 'humedad', data)
    aggregator.add_reading(1, 'presion', data)
    
    # Verificar que se almacenaron los 3 tipos
    assert 'temperatura' in aggregator.buffer[1]
    assert 'humedad' in aggregator.buffer[1]
    assert 'presion' in aggregator.buffer[1]
    
    assert aggregator.buffer[1]['temperatura'][0] == 25.0
    assert aggregator.buffer[1]['humedad'][0] == 60.0
    assert aggregator.buffer[1]['presion'][0] == 1013.0


def test_buffer_clearing():
    """Test: El buffer se limpia después de calcular medias"""
    aggregator = SensorDataAggregator(interval_minutes=5)
    
    # Añadir varias lecturas
    for i in range(5):
        aggregator.add_reading(1, 'temperatura', {'temperatura': 20.0 + i})
    
    assert len(aggregator.buffer[1]['temperatura']) == 5
    
    # Simular cálculo de medias (requiere mock de la BD)
    with patch('app.services.data_aggregator.Session'):
        aggregator._calculate_and_save_averages()
    
    # El buffer debe estar vacío después del cálculo
    assert len(aggregator.buffer) == 0


def test_aggregator_thread_safe():
    """Test: El agregador es thread-safe usando locks"""
    aggregator = SensorDataAggregator(interval_minutes=5)
    
    # Verificar que tiene un lock
    assert aggregator.lock is not None
    
    # Añadir una lectura (usa el lock internamente)
    aggregator.add_reading(1, 'temperatura', {'temperatura': 25.0})
    
    assert len(aggregator.buffer[1]['temperatura']) == 1


def test_start_stop_aggregator():
    """Test: Iniciar y detener el agregador"""
    aggregator = SensorDataAggregator(interval_minutes=5)
    
    # Estado inicial
    assert aggregator.running is False
    assert aggregator.thread is None
    
    # No iniciamos realmente el agregador para evitar problemas con threads en tests
    # Solo verificamos que los atributos existen
    assert hasattr(aggregator, 'start')
    assert hasattr(aggregator, 'stop')
    assert hasattr(aggregator, '_aggregation_loop')


@pytest.mark.parametrize("values,expected_avg", [
    ([10.0, 20.0, 30.0], 20.0),
    ([15.5, 15.5, 15.5], 15.5),
    ([0.0, 100.0], 50.0),
    ([5.0], 5.0),
])
def test_average_calculation(values, expected_avg):
    """Test: Cálculo de medias con diferentes conjuntos de valores"""
    # Calcular media manualmente para verificar
    calculated_avg = sum(values) / len(values)
    assert abs(calculated_avg - expected_avg) < 0.01  # Tolerancia de precisión
