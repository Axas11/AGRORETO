# tests/test_models.py
"""
Tests para los modelos de datos
"""
import pytest
from datetime import datetime

from app.models import User, Parcel, Sensor, SensorData, Alert


def test_create_user(session):
    """Test: Crear usuario en la base de datos"""
    user = User(
        username="newuser",
        password_hash="hashed_password",
        role="technician"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    assert user.id is not None
    assert user.username == "newuser"
    assert user.role == "technician"
    assert user.created_at is not None


def test_create_parcel(session, test_user):
    """Test: Crear parcela asociada a un usuario"""
    parcel = Parcel(
        name="North Field",
        location="40.7128, -74.0060",
        area=250.5,
        owner_id=test_user.id
    )
    session.add(parcel)
    session.commit()
    session.refresh(parcel)
    
    assert parcel.id is not None
    assert parcel.name == "North Field"
    assert parcel.area == 250.5
    assert parcel.owner_id == test_user.id


def test_create_sensor(session, test_parcel):
    """Test: Crear sensor asociado a una parcela"""
    sensor = Sensor(
        id_code="TEMP-001",
        parcel_id=test_parcel.id,
        type="temperature",
        unit="°C",
        description="Temperature sensor",
        threshold_low=5.0,
        threshold_high=35.0,
        active=True,
        mqtt_topic="farm/temp/001"
    )
    session.add(sensor)
    session.commit()
    session.refresh(sensor)
    
    assert sensor.id is not None
    assert sensor.id_code == "TEMP-001"
    assert sensor.active is True
    assert sensor.threshold_low == 5.0


def test_create_sensor_data(session, test_sensor):
    """Test: Crear lectura de sensor"""
    data = SensorData(
        sensor_id=test_sensor.id,
        value=25.5,
        raw='{"temp": 25.5}'
    )
    session.add(data)
    session.commit()
    session.refresh(data)
    
    assert data.id is not None
    assert data.sensor_id == test_sensor.id
    assert data.value == 25.5
    assert data.timestamp is not None


def test_create_alert(session, test_sensor):
    """Test: Crear alerta de sensor"""
    alert = Alert(
        sensor_id=test_sensor.id,
        type="HIGH",
        message="Temperature too high",
        acknowledged=False
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    
    assert alert.id is not None
    assert alert.sensor_id == test_sensor.id
    assert alert.type == "HIGH"
    assert alert.acknowledged is False
    assert alert.timestamp is not None


def test_sensor_thresholds(test_sensor):
    """Test: Verificar umbrales del sensor"""
    assert test_sensor.threshold_low < test_sensor.threshold_high
    
    # Valor dentro de rango
    value_ok = 20.0
    assert test_sensor.threshold_low < value_ok < test_sensor.threshold_high
    
    # Valor fuera de rango (alto)
    value_high = 35.0
    assert value_high > test_sensor.threshold_high
    
    # Valor fuera de rango (bajo)
    value_low = 5.0
    assert value_low < test_sensor.threshold_low
