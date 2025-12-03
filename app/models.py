# app/models.py
from datetime import datetime

import reflex as rx
import sqlmodel
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    password_hash: str
    role: str  # farmer, technician, registered (pending approval)
    created_at: datetime = Field(default_factory=datetime.now)

class Parcel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    location: str
    area: float
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)

class Sensor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    id_code: str
    parcel_id: int = Field(foreign_key="parcel.id")
    type: str  # temperatura, humedad_ambiente, humedad_suelo, etc.
    unit: str
    description: str
    threshold_low: float
    threshold_high: float
    active: bool = True
    
    # Nuevo campo para MQTT
    mqtt_topic: str = Field(default="Awi7LJfyyn6LPjg/15046220")

class SensorData(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensor.id")
    timestamp: datetime = Field(default_factory=datetime.now)
    value: float
    raw: str  # Aquí guardaremos el JSON completo del MAIoTA

class Alert(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensor.id")
    timestamp: datetime = Field(default_factory=datetime.now)
    type: str  # low, high, offline, etc.
    message: str
    acknowledged: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
