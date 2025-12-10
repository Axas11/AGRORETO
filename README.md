# 🌱 AGRORETO - Sistema de Monitoreo de Sensores Agrícolas

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Reflex](https://img.shields.io/badge/Reflex-0.6+-purple)
```markdown
# 🌱 AGRORETO - Sistema de Monitoreo de Sensores Agrícolas

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Reflex](https://img.shields.io/badge/Reflex-0.6+-purple)
![License](https://img.shields.io/badge/License-MIT-green)

Sistema web de monitoreo en tiempo real para sensores agrícolas IoT basado en la plataforma **MAIoTA**. Permite gestionar parcelas, sensores y visualizar datos ambientales con alertas automáticas.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [API REST](#-api-rest)
- [Arquitectura](#-arquitectura)
- [Despliegue](#-despliegue)

---

## ✨ Características

### Funcionalidades Principales

- 🔐 **Autenticación de usuarios** con roles (Agricultor y Técnico/Visor)
- 🆕 **Registro con aprobación administrativa**: los nuevos usuarios reciben el rol `registered` y deben ser aprobados por un administrador antes de obtener acceso completo.
- 📊 **Dashboard en tiempo real** con métricas y gráficos interactivos
- 🌾 **Gestión de parcelas** - Crear, editar y eliminar parcelas agrícolas
- 📡 **Monitoreo de sensores** - Temperatura, humedad, CO₂, luminosidad, COV, NOx
- 📈 **Visualización histórica** - Gráficos de tendencias por rango de fechas
- ⚠️ **Sistema de alertas** - Notificaciones cuando se superan umbrales configurables
- 🔄 **Integración MQTT** - Recepción en tiempo real de datos de sensores MAIoTA
- 🌐 **API REST** - Endpoints para integración con sistemas externos
- 📱 **Interfaz responsiva** - Diseño adaptativo para móviles, tablets y desktop

### Tipos de Sensores Soportados

| Tipo | Unidad | Descripción |
|------|--------|-------------|
| Temperatura | °C | Temperatura ambiente |
| Humedad Suelo | % | Nivel de humedad del terreno |
| Humedad Ambiente | % | Humedad relativa del aire |
| Luminosidad | Lux | Intensidad de luz |
| CO₂ | ppm | Concentración de dióxido de carbono |
| COV | Index | Compuestos orgánicos volátiles |
| NOx | Index | Óxidos de nitrógeno |

---

## 🛠 Tecnologías

### Backend
- **Python 3.10+** - Lenguaje base
- **Reflex** - Framework full-stack para Python
- **SQLModel** - ORM para SQLite
- **Paho MQTT** - Cliente MQTT para sensores IoT
- **FastAPI/Starlette** - API REST integrada

### Frontend
- **Reflex Components** - UI components en Python
- **Tailwind CSS** - Estilos y diseño responsivo
- **React Router** - Navegación (generado por Reflex)

### Base de Datos
- **SQLite** - Base de datos relacional embebida

### IoT
- **Broker MQTT** - broker.emqx.io
- **MAIoTA Platform** - Sensores agrícolas

---

## 📦 Requisitos Previos

- Python 3.10 o superior
- pip (gestor de paquetes Python)
- Node.js 20.19+ (instalado automáticamente por Reflex)
- Conexión a Internet (para MQTT broker)

---

## 🚀 Instalación

### 1. Clonar el repositorio

git clone https://github.com/Axas11/AGRORETO.git
cd AGRORETO

### 2. Crear entorno virtual

python3 -m venv venv
source venv/bin/activate # En Windows: venv\Scripts\activate

### 3. Instalar dependencias

pip install -r requirements.txt

### 4. Inicializar base de datos

Si usas Alembic:

reflex db init
reflex db migrate

Si no usas migraciones (entorno de desarrollo), puedes crear las tablas y datos de ejemplo ejecutando el script de seed:

python3 -c "from app.utils import seed_database; seed_database()"

Este comando ejecuta `SQLModel.metadata.create_all(engine)` internamente y crea tablas nuevas como `ParcelTechnician` si están definidas en `app/models.py`.

### 5. Ejecutar la aplicación

reflex run

La aplicación estará disponible en:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

---

## ⚙️ Configuración

### Usuarios por Defecto

El sistema crea automáticamente estos usuarios de prueba:

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | admin123 | Agricultor (full access) |
| tech | tech123 | Técnico (solo lectura) |

---

## 📖 Uso

### 1. Iniciar Sesión

Accede a http://localhost:3000 e inicia sesión con las credenciales por defecto.

Si te registras como nuevo usuario, recibirás el rol `registered` y no tendrás acceso completo hasta que un administrador apruebe la cuenta. El administrador puede gestionar usuarios desde **Admin → Users**.

### 2. Crear una Parcela

1. Ve a **"Parcels"** en el menú
2. Click en **"Add Parcel"**
3. Completa los datos: nombre, ubicación, área (m²)
4. Guardar

### 3. Añadir Sensores

1. Entra en el detalle de una parcela
2. Click en **"Add Sensor"**
3. Configura:
   - Código del sensor (ej: `M-TEMP-01`)
   - Tipo (temperatura, humedad, etc.)
   - Topic MQTT del sensor MAIoTA
   - Umbrales mínimo y máximo para alertas
4. Guardar

Los datos comenzarán a recibirse automáticamente si el sensor está activo.

### 4. Visualizar Datos

- **Dashboard**: Vista general con últimas lecturas y alertas
- **Detalle de Sensor**: Gráfico histórico con filtros de fecha
- **Alertas**: Listado de todas las alertas generadas

### 5. Asignar Técnicos a Parcelas

Los propietarios (agricultores) pueden asignar técnicos a una parcela desde la vista de detalle de la misma. Los técnicos asignados obtendrán visibilidad de la parcela y sus sensores.

1. Accede al detalle de la parcela como propietario
2. En la sección "Técnicos asignados" selecciona un técnico disponible
3. Click en "Asignar técnico"
4. Para remover un técnico, haz click en "Quitar" junto a su nombre

---

## 🔌 API REST

La aplicación expone una API REST completa en `http://localhost:8000/api`.

### Endpoints Principales

#### Sensores

Listar todos los sensores
GET /api/sensors

Obtener datos de un sensor
GET /api/sensors/{sensor_id}/data?limit=100

Enviar nueva lectura
POST /api/sensors/{sensor_id}/data
Content-Type: application/json
{
"value": 25.5,
"timestamp": "2025-11-25T10:00:00Z"
}

#### Parcelas

Listar parcelas
GET /api/parcels

Sensores de una parcela
GET /api/parcels/{parcel_id}/sensors

Crear parcela
POST /api/parcels
Content-Type: application/json
{
"name": "Parcela Norte",
"location": "Campo A1",
"area": 5000.0,
"owner_id": 1
}

#### Alertas

Listar alertas no reconocidas
GET /api/alerts?acknowledged=false

Reconocer alerta
POST /api/alerts/{alert_id}/acknowledge

### Ejemplos con curl

Obtener todos los sensores
curl http://localhost:8000/api/sensors

Últimas 10 lecturas de un sensor
curl "http://localhost:8000/api/sensors/1/data?limit=10"

Crear nueva lectura
curl -X POST http://localhost:8000/api/sensors/1/data
-H "Content-Type: application/json"
-d '{"value": 18.5}'

---

## 🏗 Arquitectura

### Estructura del Proyecto

AGRORETO/
├── app/
│ ├── api/
│ │ └── routes.py # API REST endpoints
│ ├── components/
│ │ ├── charts.py # Componentes de gráficos
│ │ ├── navbar.py # Barra de navegación
│ │ └── styles.py # Estilos reutilizables
│ ├── models.py # Modelos de base de datos
│ ├── pages/
│ │ ├── admin_users.py # Gestión de usuarios (admin)
│ │ ├── alerts.py # Gestión de alertas
│ │ ├── dashboard.py # Dashboard principal
│ │ ├── index.py # Página de inicio
│ │ ├── info.py # Página de información
│ │ ├── login_form.py # Formulario de login
│ │ ├── parcel_detail.py # Detalle de parcela y sensores
│ │ ├── parcels.py # Listado de parcelas
│ │ ├── register_form.py # Formulario de registro
│ │ └── sensor_detail.py # Gráficos históricos de sensores
│ ├── services/
│ │ ├── data_aggregator.py # Agregador de datos (medias cada 5 min)
│ │ └── maiota_client.py # Cliente MQTT para sensores
│ ├── states/
│ │ ├── alert_state.py # Estado de alertas
│ │ ├── auth_state.py # Estado de autenticación
│ │ ├── dashboard_state.py # Estado del dashboard
│ │ ├── parcel_state.py # Gestión de parcelas
│ │ ├── sensor_history_state.py # Histórico de sensores
│ │ └── sensor_state.py # Gestión de sensores
│ ├── utils.py # Utilidades y conexión BD
│ └── app.py # Configuración principal
├── alembic/ # Migraciones de base de datos
├── assets/ # Imágenes y recursos
├── clean_alerts.py # Script para limpiar alertas
├── reflex.db # Base de datos SQLite
├── rxconfig.py # Configuración de Reflex
├── requirements.txt # Dependencias Python
└── AGREGACION_DATOS.md # Documentación del sistema de agregación

### Flujo de Datos MQTT

[Sensor MAIoTA]
↓ MQTT (5s interval)
[Broker EMQX] → [maiota_client.py]
↓ Callback
[save_sensor_reading_direct()]
↓ SQLite
[Database] → [States] → [UI Components]

---

## 🚢 Despliegue

### Producción

Optimizar para producción
reflex export

Variables de entorno recomendadas
export DATABASE_URL=sqlite:///reflex.db
export MQTT_BROKER=broker.emqx.io
export MQTT_PORT=1883

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

---

## 👥 Equipo

**Equipo Agrotech - Reto MAIoTA**

- GitHub: [@Francisco Jose Rodriguez Guerra](https://github.com/Axas11)
- GitHub: [@Rafael Ballesteros Padial](https://github.com/GomasDev)
- GitHUb: [@Victor Alvarez Cabrera](https://github.com/VictorAlvarezCabrera)
- GitHub: [@Fernando Mansilla Hidalgo  ](https://github.com/Fermh97)
- Proyecto: [AGRORETO](https://github.com/Axas11/AGRORETO)

---

**Desarrollado con ❤️ para la agricultura inteligente**
```