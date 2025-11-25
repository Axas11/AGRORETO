# app/services/__init__.py
"""
Módulo de servicios de la aplicación Agrotech.
Contiene el cliente MQTT para sensores MAIoTA.
"""

from app.services.maiota_client import maiota_client

__all__ = ['maiota_client']
