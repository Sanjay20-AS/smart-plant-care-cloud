# Cloud-Connected Smart Plant Care & Watering System

A production-ready IoT platform for monitoring and automating plant watering with real-time sensor data, intelligent watering decisions, and cloud-based alerts.

## 🌱 Features

- **Real-time Monitoring**: Live sensor dashboard with moisture, temperature, and humidity
- **Intelligent Watering**: Automated decision engine with cooldown and daily limits
- **Alert System**: Automatic alerts for moisture threshold violations
- **Device Management**: Register and manage multiple IoT sensors per plant
- **User Authentication**: Secure Supabase Auth integration
- **Historical Analytics**: Sensor data trends and watering history
- **Multi-plant Support**: Manage unlimited plants with personalized thresholds
- **Responsive UI**: React dashboard with charts and real-time updates

## 📊 Project Status

✅ **Complete** - All features implemented and tested:
- Phase 1-6: Full production system
- 80 backend tests passing
- Real-time sensor simulator
- Complete frontend dashboard
- Supabase authentication
- Alert generation and management
- Device registration UI
- Watering logic with safeguards

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend (Vite)                      │
│         Dashboard, Plant Management, Alerts Display          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/JSON
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                        │
│    REST API, Authentication, Business Logic, DB Access      │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQL
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          Supabase PostgreSQL Database                        │
│    Plants, Devices, Sensors, Readings, Alerts, Events       │
└─────────────────────────────────────────────────────────────┘
                       ▲
                       │ POST readings
                       │
┌──────────────────────┴──────────────────────────────────────┐
│          Python Sensor Simulator                            │
│     Generates realistic plant sensor data                    │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11, FastAPI, Pydantic, SQLAlchemy |
| **Frontend** | React 18, Vite, Recharts, Axios |
| **Database** | Supabase PostgreSQL |
| **Authentication** | Supabase Auth (JWT) |
| **Testing** | Pytest (80 tests) |
| **IoT Simulation** | Python requests |
| **Deployment** | Vercel (Frontend), Railway/Render (Backend) |

## 📁 Project Structure

```
cloud-connected-smart-plant-care-and-watering-system/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── auth.py            # Supabase JWT authentication
│   │   ├── database.py        # Database session management
│   │   ├── main.py            # Application entry point
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── routes.py          # 28 REST API endpoints
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── security.py        # Device & user authorization
│   │   ├── services.py        # Business logic (watering, alerts)
│   │   ├── user_scope.py      # User-based data scoping
│   │   └── __init__.py
│   ├── migrations/            # Alembic database migrations
│   │   └── versions/
│   │       ├── 001_add_user_id_column.py
│   │       └── 002_extend_user_id_column.py
│   ├── tests/                 # 80 unit and integration tests
│   ├── requirements.txt       # Python dependencies
│   ├── pytest.ini            # Pytest configuration
│   ├── config.py             # Settings from environment
│   ├── alembic.ini           # Database migration config
│   └── smartplant.db         # Local SQLite (dev only)
│
├── frontend/                  # React Vite frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── App.jsx         # Root component with auth
│   │   │   ├── LoginPage.jsx   # Supabase login
│   │   │   ├── RegisterPage.jsx # User registration
│   │   │   ├── PlantsPage.jsx  # Plant listing
│   │   │   └── PlantDetailsPage.jsx # Plant details with alerts
│   │   ├── components/         # Reusable UI components
│   │   ├── services/           # API client
│   │   ├── styles/             # CSS modules
│   │   └── App.jsx             # Root component
│   ├── package.json           # Node dependencies
│   ├── vite.config.js         # Vite configuration
│   └── index.html             # HTML entry point
│
├── sensor_simulator/          # Python IoT sensor simulator
│   ├── simulator.py           # Main simulator logic
│   ├── config.py              # Configuration
│   └── .env                   # Simulator settings
│
├── docker/                    # Docker configuration
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── docs/                      # Project documentation
│   ├── ARCHITECTURE.md        # System architecture details
│   ├── DATABASE.md            # Database schema documentation
│   └── API.md                 # Complete API reference
│
├── config/                    # Environment templates
│   └── development.env
│
├── .github/workflows/         # CI/CD pipelines
│   └── ci.yml                 # GitHub Actions workflow
│
├── vercel.json                # Vercel deployment config
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Supabase project (free tier at https://supabase.com)

### 1. Clone & Setup Backend

```bash
git clone https://github.com/Sanjay20-AS/smart-plant-care-cloud.git
cd smart-plant-care-cloud/backend

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase credentials
alembic upgrade head

python -m uvicorn app.main:app --reload --port 8000
```

API will be available at `http://localhost:8000`

### 2. Setup Frontend

```bash
cd ../frontend

npm install
cp .env.example .env
# Edit .env with your API and Supabase URLs

npm run dev
```

Frontend will be available at `http://localhost:5173`

### 3. Run Sensor Simulator

```bash
cd ../sensor_simulator

cp .env.example .env
# Edit .env to set DEVICE_ID, PLANT_ID, MOISTURE_MIN/MAX, etc.

python simulator.py
```

The simulator will start sending readings every 60 seconds (configurable).

## 🔧 Configuration

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/db_name

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
REQUIRE_AUTH=true

# Watering Logic
DAILY_WATERING_LIMIT=3
WATERING_COOLDOWN_MINUTES=60
WATERING_DURATION_SECONDS=30
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_KEY=your-anon-key
```

### Sensor Simulator (.env)

```env
BACKEND_URL=http://localhost:8000/api/v1
DEVICE_ID=sensor_001
PLANT_ID=plant_001
SENSOR_INTERVAL=60
MOISTURE_MIN=20
MOISTURE_MAX=25
TEMPERATURE_MIN=15
TEMPERATURE_MAX=35
```

## 📚 API Documentation

### Complete API Reference

Access interactive API docs at `http://localhost:8000/docs` (Swagger UI)

**Key Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/plants` | Create a plant |
| GET | `/plants` | List user's plants |
| GET | `/plants/{id}` | Get plant details |
| POST | `/devices` | Register IoT device |
| POST | `/sensor-readings` | Ingest sensor data (device auth) |
| POST | `/watering/decision/{id}` | Get watering eligibility |
| POST | `/watering/execute/{id}` | Execute watering |
| GET | `/alerts` | List user's alerts |
| GET | `/analytics/plant/{id}` | Get plant analytics |

See `docs/API.md` for complete endpoint documentation with examples.

## 🧪 Testing

### Run All Tests

```bash
cd backend
pytest tests/ -v
```

### Test Coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

**Current Coverage:**
- 80 unit and integration tests
- Authentication & authorization
- Database models and relationships
- API endpoints and request validation
- Watering logic and safeguards
- Alert generation
- Analytics calculations

## 🌐 Deployment

### Frontend Deployment (Vercel)

```bash
cd frontend
npm run build
vercel deploy
```

Environment variables needed in Vercel:
- `VITE_API_URL`: Backend API URL
- `VITE_SUPABASE_URL`: Supabase project URL
- `VITE_SUPABASE_KEY`: Supabase anon key

### Backend Deployment (Railway/Render)

Recommended services:
- **Railway**: `railway up` (simple)
- **Render**: Connect GitHub repo for auto-deploy
- **Heroku**: `git push heroku main`

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `REQUIRE_AUTH`: Set to `true` for production

### Docker Deployment

```bash
docker-compose -f docker/docker-compose.yml up
```

## 📖 Documentation

- **API Reference**: `docs/API.md` - Comprehensive endpoint documentation
- **Architecture**: `docs/ARCHITECTURE.md` - System design and components
- **Database**: `docs/DATABASE.md` - Schema and relationships

## 🔐 Security

- **Authentication**: Supabase JWT tokens with RS256 signature verification
- **Device Auth**: Device ID validation on sensor ingestion endpoints
- **User Scoping**: All queries filtered by user ID
- **Input Validation**: Pydantic schemas for all requests
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy ORM
- **CORS**: Configured for frontend access
- **Env Secrets**: .env files excluded from version control

## 📊 System Features

### Plant Management
- Create/update/delete plants
- Set custom moisture thresholds
- Track multiple plants per user
- Monitor plant health status

### Device Management
- Register IoT sensors (device_id)
- Track device status (active/inactive)
- Monitor last communication time
- Delete inactive devices

### Sensor Integration
- Ingest real-time sensor readings
- Store historical data
- Calculate statistics (min/max/avg)
- Generate alerts on threshold violations

### Intelligent Watering
- Automatic eligibility checks
- Moisture-based triggers
- Daily limit safeguard
- Cooldown period enforcement
- Manual watering override

### Alert System
- Real-time alerts for moisture violations
- Duplicate alert prevention
- Status tracking (active/acknowledged/resolved)
- Severity levels (warning/critical)
- Alert history with timestamps

### Analytics
- Plant-specific metrics
- Sensor trend analysis
- Watering history
- System-wide summaries
- 24-hour activity reports

## 🤝 Contributing

This project is part of a smart IoT ecosystem. Contributions are welcome for:
- Additional sensor types (humidity, light, CO2)
- Advanced watering algorithms
- Mobile app frontend
- Multi-zone garden management
- Integration with smart home platforms

## 📝 License

MIT License - See LICENSE file for details

## 🙋 Support

For issues, questions, or suggestions:
1. Check existing documentation in `/docs`
2. Review API documentation at `/docs` (when backend running)
3. Check test examples in `/tests` for usage patterns

## 🗺️ Roadmap

**v1.0** (Current) ✅
- Core plant monitoring
- IoT device integration
- Real-time dashboards
- Alert system

**v2.0** (Planned)
- Mobile app (React Native)
- Advanced scheduling
- Multi-user groups/households
- Integration with weather APIs
- Soil nutrient tracking

**v3.0** (Future)
- Computer vision for plant health
- ML-based watering optimization
- Voice control integration
- Multiple garden locations

---

**Version**: 1.0.0  
**Last Updated**: November 2026  
**Status**: Production Ready ✅
