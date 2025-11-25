import reflex as rx
from passlib.context import CryptContext
from sqlmodel import select, create_engine, SQLModel, Session
from app.models import User, Parcel, Sensor, SensorData, Alert
import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DATABASE_URL = "sqlite:///reflex.db"
engine = create_engine(DATABASE_URL)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def seed_database():
    """Initialize the database with sample data if it's empty."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        result = session.exec(select(User)).first()
        if result:
            return
        print("Seeding database with initial data...")
        farmer = User(
            username="admin", password_hash=get_password_hash("admin123"), role="farmer"
        )
        tech = User(
            username="tech",
            password_hash=get_password_hash("tech123"),
            role="technician",
        )
        session.add(farmer)
        session.add(tech)
        session.commit()
        session.refresh(farmer)
        session.refresh(tech)
        p1 = Parcel(
            name="North Field Alpha",
            location="34.0522, -118.2437",
            area=150.5,
            owner_id=farmer.id,
        )
        p2 = Parcel(
            name="Green Valley South",
            location="36.1699, -115.1398",
            area=85.2,
            owner_id=farmer.id,
        )
        session.add(p1)
        session.add(p2)
        session.commit()
        session.refresh(p1)
        session.refresh(p2)
        sensors = [
            Sensor(
                id_code="S-TEMP-01",
                parcel_id=p1.id,
                type="temperature",
                unit="°C",
                description="Air Temp Main",
                threshold_low=10.0,
                threshold_high=35.0,
            ),
            Sensor(
                id_code="S-SOIL-01",
                parcel_id=p1.id,
                type="soil_humidity",
                unit="%",
                description="Soil Moisture Row 1",
                threshold_low=30.0,
                threshold_high=80.0,
            ),
            Sensor(
                id_code="S-LUM-01",
                parcel_id=p1.id,
                type="luminosity",
                unit="lux",
                description="Sunlight Sensor",
                threshold_low=500.0,
                threshold_high=10000.0,
            ),
            Sensor(
                id_code="S-TEMP-02",
                parcel_id=p2.id,
                type="temperature",
                unit="°C",
                description="Greenhouse Temp",
                threshold_low=15.0,
                threshold_high=30.0,
            ),
            Sensor(
                id_code="S-HUM-02",
                parcel_id=p2.id,
                type="ambient_humidity",
                unit="%",
                description="Air Humidity",
                threshold_low=40.0,
                threshold_high=70.0,
            ),
            Sensor(
                id_code="S-SOIL-02",
                parcel_id=p2.id,
                type="soil_humidity",
                unit="%",
                description="Soil Moisture Row 4",
                threshold_low=30.0,
                threshold_high=80.0,
            ),
        ]
        for s in sensors:
            session.add(s)
        session.commit()
        for s in sensors:
            session.refresh(s)
        import random

        s1 = sensors[0]
        data_points = []
        for i in range(10):
            val = 20.0 + random.uniform(-5, 5)
            data_points.append(SensorData(sensor_id=s1.id, value=val, raw=str(val)))
        high_val = 40.0
        data_points.append(
            SensorData(sensor_id=s1.id, value=high_val, raw=str(high_val))
        )
        for d in data_points:
            session.add(d)
        alert = Alert(
            sensor_id=s1.id,
            type="HIGH",
            message=f"Temperature exceeding threshold: {high_val}°C",
            acknowledged=False,
        )
        session.add(alert)
        session.commit()
        print("Database seeding complete.")