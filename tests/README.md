# Tests del Proyecto AGRORETO

Este directorio contiene los tests unitarios del proyecto.

## Estructura de Tests

```
tests/
├── __init__.py                 # Inicialización del paquete
├── conftest.py                 # Fixtures compartidas
├── test_models.py              # Tests de modelos de BD
├── test_utils.py               # Tests de funciones de utilidad
├── test_data_aggregator.py     # Tests del agregador de datos
└── test_maiota_client.py       # Tests del cliente MQTT
```

## Ejecutar Tests

### Instalar dependencias de testing

```bash
pip install -r requirements-test.txt
```

### Ejecutar todos los tests

```bash
pytest
```

### Ejecutar tests con cobertura

```bash
pytest --cov=app --cov-report=html
```

### Ejecutar tests específicos

```bash
# Un archivo específico
pytest tests/test_models.py

# Una función específica
pytest tests/test_models.py::test_create_user

# Tests que coincidan con un patrón
pytest -k "password"
```

### Opciones útiles

```bash
# Mostrar output detallado
pytest -v

# Mostrar print statements
pytest -s

# Detener en el primer fallo
pytest -x

# Ejecutar últimos tests fallidos
pytest --lf

# Mostrar tests más lentos
pytest --durations=10
```

## Cobertura de Tests

Los tests cubren:

- ✅ **Modelos de datos**: Creación de usuarios, parcelas, sensores, datos y alertas
- ✅ **Utilidades**: Hash y verificación de contraseñas
- ✅ **Agregador de datos**: Buffer, cálculo de medias, thread safety
- ✅ **Cliente MQTT**: Parseo de payloads, gestión de sensores, callbacks

## Fixtures Disponibles

Definidas en `conftest.py`:

- `engine`: Motor de BD en memoria
- `session`: Sesión de BD para cada test
- `test_user`: Usuario de prueba
- `test_parcel`: Parcela de prueba
- `test_sensor`: Sensor de prueba

## Escribir Nuevos Tests

### Ejemplo básico

```python
def test_example(session):
    """Test: Descripción breve"""
    # Arrange (preparar)
    user = User(username="test", password_hash="hash", role="farmer")
    
    # Act (ejecutar)
    session.add(user)
    session.commit()
    
    # Assert (verificar)
    assert user.id is not None
```

### Con fixtures

```python
def test_with_fixture(test_user):
    """Test usando fixture de usuario"""
    assert test_user.username == "testuser"
    assert test_user.role == "farmer"
```

### Con mocks

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test usando mocks"""
    with patch('app.services.maiota_client.mqtt.Client'):
        client = MAIoTAMultiSensorClient()
        assert client is not None
```

## Buenas Prácticas

1. **Un concepto por test**: Cada test debe verificar una cosa específica
2. **Nombres descriptivos**: `test_create_user_with_valid_data`
3. **AAA pattern**: Arrange, Act, Assert
4. **Fixtures para setup**: Reutilizar configuración común
5. **Mocks para dependencias**: Aislar el código bajo test
6. **Tests independientes**: No deben depender del orden de ejecución

## CI/CD

Para integración continua, agregar al pipeline:

```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install -r requirements-test.txt
    pytest --cov=app --cov-report=xml
```
