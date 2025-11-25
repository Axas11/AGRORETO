import reflex as rx
from datetime import datetime
import sqlmodel
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    password_hash: str
    role: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Parcel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    location: str
    area: float
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Sensor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    id_code: str
    parcel_id: int = Field(foreign_key="parcel.id")
    type: str
    unit: str
    description: str
    threshold_low: float
    threshold_high: float
    active: bool = True


class SensorData(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensor.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    value: float
    raw: str


class Alert(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sensor_id: int = Field(foreign_key="sensor.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: str
    message: str
    acknowledged: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)