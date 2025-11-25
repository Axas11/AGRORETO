from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from starlette.requests import Request
from starlette.responses import JSONResponse  # ← AÑADIR ESTO

from app.models import Parcel, Sensor, SensorData
from app.utils import engine

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
def get_parcels(request: Request):
    """List all registered parcels."""
    with Session(engine) as session:
        parcels = session.exec(select(Parcel)).all()
        data = [
            {"id": p.id, "name": p.name, "location": p.location, "area": p.area, "owner_id": p.owner_id}
            for p in parcels
        ]
        return JSONResponse(content=data)  # ← CAMBIO AQUÍ

@router.get("/parcels/{parcel_id}/sensors")
def get_parcel_sensors(request: Request, parcel_id: int):
    """Get all sensors associated with a specific parcel."""
    with Session(engine) as session:
        sensors = session.exec(select(Sensor).where(Sensor.parcel_id == parcel_id)).all()
        data = [
            {
                "id": s.id, "id_code": s.id_code, "type": s.type, "unit": s.unit,
                "description": s.description, "threshold_low": s.threshold_low,
                "threshold_high": s.threshold_high, "active": s.active
            } for s in sensors
        ]
        return JSONResponse(content=data)

@router.get("/sensors")
def get_sensors(request: Request):
    """List all sensors in the system."""
    with Session(engine) as session:
        sensors = session.exec(select(Sensor)).all()
        data = [
            {
                "id": s.id, "id_code": s.id_code, "parcel_id": s.parcel_id,
                "type": s.type, "unit": s.unit, "description": s.description,
                "threshold_low": s.threshold_low, "threshold_high": s.threshold_high,
                "active": s.active, "mqtt_topic": s.mqtt_topic
            } for s in sensors
        ]
        return JSONResponse(content=data)

@router.post("/parcels")
def create_parcel(request: Request, parcel: ParcelCreate):
    """Create a new parcel."""
    with Session(engine) as session:
        db_parcel = Parcel.model_validate(parcel)
        session.add(db_parcel)
        session.commit()
        session.refresh(db_parcel)
        return JSONResponse(content={
            "id": db_parcel.id, "name": db_parcel.name,
            "location": db_parcel.location, "area": db_parcel.area
        })

@router.post("/sensors")
def create_sensor(request: Request, sensor: SensorCreate):
    """Register a new sensor."""
    with Session(engine) as session:
        db_sensor = Sensor.model_validate(sensor)
        session.add(db_sensor)
        session.commit()
        session.refresh(db_sensor)
        return JSONResponse(content={
            "id": db_sensor.id, "id_code": db_sensor.id_code, "type": db_sensor.type
        })

@router.post("/sensors/{sensor_id}/data")
def receive_sensor_data(request: Request, sensor_id: int, data: SensorDataInput):
    """Submit a new data reading for a sensor."""
    with Session(engine) as session:
        sensor = session.get(Sensor, sensor_id)
        if not sensor:
            return JSONResponse(status_code=404, content={"detail": "Sensor not found"})
        
        new_data = SensorData(
            sensor_id=sensor_id,
            timestamp=data.timestamp or datetime.utcnow(),
            value=data.value,
            raw=str(data.value),
        )
        session.add(new_data)
        session.commit()
        session.refresh(new_data)
        return JSONResponse(content={"status": "success", "data_id": new_data.id})

@router.get("/sensors/{sensor_id}/data")
def get_sensor_history(
    request: Request,
    sensor_id: int,
    start: Optional[datetime] = Query(None, alias="from"),
    end: Optional[datetime] = Query(None, alias="to"),
    limit: int = 100,
):
    """Get historical data for a specific sensor."""
    with Session(engine) as session:
        query = select(SensorData).where(SensorData.sensor_id == sensor_id)
        if start:
            query = query.where(SensorData.timestamp >= start)
        if end:
            query = query.where(SensorData.timestamp <= end)
        query = query.order_by(SensorData.timestamp.desc()).limit(limit)
        results = session.exec(query).all()
        
        data = [
            {
                "id": r.id, "sensor_id": r.sensor_id,
                "timestamp": r.timestamp.isoformat(),
                "value": r.value, "raw": r.raw
            } for r in results
        ]
        return JSONResponse(content=data)

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(request: Request, alert_id: int):
    """Acknowledge a specific alert."""
    with Session(engine) as session:
        from app.models import Alert
        alert = session.get(Alert, alert_id)
        if not alert:
            return JSONResponse(status_code=404, content={"detail": "Alert not found"})
        
        alert.acknowledged = True
        session.add(alert)
        session.commit()
        return JSONResponse(content={"status": "success", "message": "Alert acknowledged"})
