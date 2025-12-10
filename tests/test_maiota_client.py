# tests/test_maiota_client.py
"""
Tests para el cliente MQTT de sensores MAIoTA
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.maiota_client import MAIoTAMultiSensorClient


def test_client_initialization():
    """Test: Inicialización del cliente MQTT"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        
        assert client.broker == "broker.emqx.io"
        assert client.port == 1883
        assert client.keepalive == 60
        assert client.is_connected is False
        assert len(client.topic_callbacks) == 0
        assert len(client.active_sensors) == 0


def test_unique_client_id():
    """Test: Cada instancia tiene un client_id único"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client1 = MAIoTAMultiSensorClient()
        client2 = MAIoTAMultiSensorClient()
        
        assert client1.client_id != client2.client_id
        assert client1.client_id.startswith("Equipo3_")
        assert client2.client_id.startswith("Equipo3_")


def test_parse_maiota_payload_valid():
    """Test: Parseo de payload MAIoTA válido"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        
        # Payload de ejemplo del formato MAIoTA
        payload = "CIoTA-D1=2603&D2=5411&D3=2542&D4=43&D5=580&D6=103&D7=1&"
        
        result = client._parse_maiota_payload(payload)
        
        assert result is not None
        assert 'temperatura' in result
        assert 'humedad_ambiente' in result
        assert 'humedad_suelo' in result
        assert 'iluminacion' in result
        assert 'co2' in result
        assert 'cov' in result
        assert 'nox' in result
        
        # Verificar conversiones
        assert result['temperatura'] == 26.03  # 2603 / 100
        assert result['humedad_ambiente'] == 54.11  # 5411 / 100
        assert result['humedad_suelo'] == 25.42  # 2542 / 100
        assert result['iluminacion'] == 4.3  # 43 / 10
        assert result['co2'] == 580
        assert result['cov'] == 103
        assert result['nox'] == 1


def test_parse_maiota_payload_invalid():
    """Test: Manejo de payload inválido"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        
        # Payload que no empieza con "CIoTA-"
        invalid_payload = "INVALID-D1=2603&D2=5411"
        
        result = client._parse_maiota_payload(invalid_payload)
        
        assert result is None


def test_parse_maiota_payload_low_humidity():
    """Test: Parseo de payload con humedad baja (flecha ↓)"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        
        # Payload con indicador de humedad baja
        payload = "CIoTA-D1=2500&D2=5000&D3=↓1500&D4=50&D5=600&D6=100&D7=2&"
        
        result = client._parse_maiota_payload(payload)
        
        assert result is not None
        assert result['humedad_suelo_baja'] is True
        assert result['humedad_suelo'] == 15.0


def test_add_sensor():
    """Test: Añadir sensor al cliente MQTT"""
    with patch('app.services.maiota_client.mqtt.Client') as mock_mqtt:
        client = MAIoTAMultiSensorClient()
        client.is_connected = True
        
        mock_client = Mock()
        client.client = mock_client
        
        callback = Mock()
        
        client.add_sensor(
            sensor_id=1,
            sensor_code="TEMP-01",
            sensor_type="temperatura",
            topic="test/topic",
            callback=callback
        )
        
        # Verificar que se registró el sensor
        assert "test/topic" in client.active_sensors
        assert client.active_sensors["test/topic"]['id'] == 1
        assert client.active_sensors["test/topic"]['code'] == "TEMP-01"
        
        # Verificar que se registró el callback
        assert "test/topic" in client.topic_callbacks
        assert client.topic_callbacks["test/topic"] == callback
        
        # Verificar que se suscribió al topic
        mock_client.subscribe.assert_called_once_with("test/topic")


def test_remove_sensor():
    """Test: Eliminar sensor del cliente MQTT"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        client.is_connected = True
        
        mock_client = Mock()
        client.client = mock_client
        
        # Añadir sensor primero
        callback = Mock()
        topic = "test/topic"
        client.add_sensor(1, "TEMP-01", "temperatura", topic, callback)
        
        # Verificar que está añadido
        assert topic in client.active_sensors
        
        # Eliminar sensor
        client.remove_sensor(topic)
        
        # Verificar que se eliminó
        assert topic not in client.active_sensors
        assert topic not in client.topic_callbacks
        
        # Verificar que se desuscribió del topic
        mock_client.unsubscribe.assert_called_once_with(topic)


def test_on_connect_success():
    """Test: Callback de conexión exitosa"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        
        mock_mqtt_client = Mock()
        client.topic_callbacks = {"test/topic": Mock()}
        
        # Simular conexión exitosa (rc=0)
        client._on_connect(mock_mqtt_client, None, None, 0)
        
        assert client.is_connected is True
        assert client.reconnect_attempts == 0
        
        # Debe resuscribirse a los topics
        mock_mqtt_client.subscribe.assert_called()


def test_on_connect_failure():
    """Test: Callback de conexión fallida"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        
        mock_mqtt_client = Mock()
        
        # Simular falla de conexión (rc!=0)
        client._on_connect(mock_mqtt_client, None, None, 5)
        
        assert client.is_connected is False


def test_on_disconnect():
    """Test: Callback de desconexión"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        client.is_connected = True
        
        # Simular desconexión inesperada (rc!=0)
        client._on_disconnect(Mock(), None, 1)
        
        assert client.is_connected is False
        assert client.reconnect_attempts == 1


def test_on_message():
    """Test: Procesamiento de mensaje MQTT"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        
        # Crear callback mock
        callback = Mock()
        topic = "test/topic"
        
        client.active_sensors[topic] = {
            'id': 1,
            'code': 'TEMP-01',
            'type': 'temperatura'
        }
        client.topic_callbacks[topic] = callback
        
        # Crear mensaje mock
        mock_msg = Mock()
        mock_msg.topic = topic
        mock_msg.payload = b"CIoTA-D1=2500&D2=5000&D3=2500&D4=50&D5=600&D6=100&D7=2&"
        
        # Procesar mensaje
        client._on_message(Mock(), None, mock_msg)
        
        # Verificar que se llamó al callback con los datos parseados
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        
        assert 'temperatura' in call_args
        assert 'sensor_code' in call_args
        assert call_args['sensor_code'] == 'TEMP-01'
        assert call_args['sensor_id'] == 1
