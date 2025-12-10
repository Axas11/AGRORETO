# tests/conftest.py
"""
Configuración y fixtures compartidas para todos los tests
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.models import User, Parcel, Sensor, SensorData, Alert
from app.utils import get_password_hash


@pytest.fixture(name="engine")
def engine_fixture():
    """
    Crea un motor de BD en memoria para tests
    """
    # Usar base de datos SQLite en memoria
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine):
    """
    Crea una sesión de BD para cada test
    """
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(session):
    """
    Crea un usuario de prueba en la BD
    """
    user = User(
        username="testuser",
        password_hash=get_password_hash("testpass123"),
        role="farmer"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_parcel")
def test_parcel_fixture(session, test_user):
    """
    Crea una parcela de prueba en la BD
    """
    parcel = Parcel(
        name="Test Parcel",
        location="Test Location",
        area=100.0,
        owner_id=test_user.id
    )
    session.add(parcel)
    session.commit()
    session.refresh(parcel)
    return parcel


@pytest.fixture(name="test_sensor")
def test_sensor_fixture(session, test_parcel):
    """
    Crea un sensor de prueba en la BD
    """
    sensor = Sensor(
        id_code="TEST-TEMP-01",
        parcel_id=test_parcel.id,
        type="temperatura",
        unit="°C",
        description="Sensor de prueba",
        threshold_low=10.0,
        threshold_high=30.0,
        active=True,
        mqtt_topic="test/topic"
    )
    session.add(sensor)
    session.commit()
    session.refresh(sensor)
    return sensor
