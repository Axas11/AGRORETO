from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.utils import engine
from app.models import Parcel, Sensor, SensorData

router = APIRouter(prefix="/api")


class SensorDataInput(BaseModel):
    timestamp: Optional[datetime] = None
    value: float
    unit: Optional[str] = None


class SensorCreate(BaseModel):
    id_code: str
    parcel_id: int
    type: str
    unit: str
    description: str
    threshold_low: float
    threshold_high: float


class ParcelCreate(BaseModel):
    name: str
    location: str
    area: float
    owner_id: int


@router.get("/parcels")
def get_parcels():
    """List all registered parcels."""
    with Session(engine) as session:
        parcels = session.exec(select(Parcel)).all()
        return parcels


@router.post("/parcels")
def create_parcel(parcel: ParcelCreate):
    """Create a new parcel."""
    with Session(engine) as session:
        db_parcel = Parcel.model_validate(parcel)
        session.add(db_parcel)
        session.commit()
        session.refresh(db_parcel)
        return db_parcel


@router.get("/parcels/{parcel_id}/sensors")
def get_parcel_sensors(parcel_id: int):
    """Get all sensors associated with a specific parcel."""
    with Session(engine) as session:
        sensors = session.exec(
            select(Sensor).where(Sensor.parcel_id == parcel_id)
        ).all()
        return sensors


@router.get("/sensors")
def get_sensors():
    """List all sensors in the system."""
    with Session(engine) as session:
        sensors = session.exec(select(Sensor)).all()
        return sensors


@router.post("/sensors")
def create_sensor(sensor: SensorCreate):
    """Register a new sensor."""
    with Session(engine) as session:
        db_sensor = Sensor.model_validate(sensor)
        session.add(db_sensor)
        session.commit()
        session.refresh(db_sensor)
        return db_sensor


@router.post("/sensors/{sensor_id}/data")
def receive_sensor_data(sensor_id: int, data: SensorDataInput):
    """Submit a new data reading for a sensor."""
    with Session(engine) as session:
        sensor = session.get(Sensor, sensor_id)
        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")
        new_data = SensorData(
            sensor_id=sensor_id,
            timestamp=data.timestamp or datetime.utcnow(),
            value=data.value,
            raw=str(data.value),
        )
        session.add(new_data)
        session.commit()
        session.refresh(new_data)
        return {"status": "success", "data_id": new_data.id}


@router.get("/sensors/{sensor_id}/data")
def get_sensor_history(
    sensor_id: int,
    start: Optional[datetime] = Query(None, alias="from"),
    end: Optional[datetime] = Query(None, alias="to"),
    limit: int = 100,
):
    """
    Get historical data for a specific sensor.

    Args:
        sensor_id: ID of the sensor
        start: Filter data from this timestamp (ISO 8601)
        end: Filter data up to this timestamp (ISO 8601)
        limit: Max number of records to return
    """
    with Session(engine) as session:
        query = select(SensorData).where(SensorData.sensor_id == sensor_id)
        if start:
            query = query.where(SensorData.timestamp >= start)
        if end:
            query = query.where(SensorData.timestamp <= end)
        query = query.order_by(SensorData.timestamp.desc()).limit(limit)
        results = session.exec(query).all()
        return results


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int):
    """
    Acknowledge a specific alert.

    Args:
        alert_id: ID of the alert to acknowledge
    """
    with Session(engine) as session:
        from app.models import Alert

        alert = session.get(Alert, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        alert.acknowledged = True
        session.add(alert)
        session.commit()
        return {"status": "success", "message": "Alert acknowledged"}