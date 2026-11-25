# Backend - FastAPI Application

Smart Plant Care backend API service built with FastAPI.

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Running the Application

### Development Mode

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will start at `http://localhost:8000`

**Available endpoints:**
- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - API documentation (ReDoc)

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── database.py      # Database configuration and session management
│   └── models.py        # SQLAlchemy ORM models
├── migrations/
│   ├── versions/        # Migration scripts
│   ├── env.py           # Alembic migration environment
│   └── alembic.ini      # Alembic configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Pytest fixtures
│   ├── test_health.py   # Health check tests
│   └── test_models.py   # Database model tests
├── config.py            # Pydantic settings
├── requirements.txt     # Python dependencies
├── requirements-lock.txt # Locked dependencies
├── .env.example         # Configuration template
├── pytest.ini           # Pytest configuration
└── smartplant.db        # SQLite database (auto-created)
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run database tests
pytest tests/test_models.py -v

# Run with coverage
pytest --cov=app tests/
```

**Test Coverage:**
- 2 health check tests
- 19 database model tests (21 total)
- Tests verify CRUD operations, relationships, constraints, and cascading deletes
- Uses in-memory SQLite database for isolation

## API Documentation

Once the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Database

### Setup

The database is automatically configured via environment variables in `.env`.

**Local SQLite (Default):**
```bash
DATABASE_URL=sqlite:///./smartplant.db
```

**PostgreSQL:**
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/smartplant
```

### Initialize Database

```bash
# Apply migrations to create schema
alembic upgrade head
```

### Database Models

5 core entities implemented with relationships:

- **Plant**: Individual plants with care thresholds
- **Device**: IoT sensors associated with plants
- **SensorReading**: Historical sensor data (moisture, temperature, humidity)
- **WateringEvent**: Watering records with trigger reasons
- **Alert**: System alerts with severity levels

For complete schema documentation, see `docs/DATABASE.md`.

## Implementation Status

✅ **Phase 2**: Foundation setup complete
- FastAPI application initialized
- Configuration system (Pydantic settings)
- Health check endpoint
- Test framework configured

✅ **Phase 3**: Database implementation complete
- SQLAlchemy ORM models (5 entities)
- Alembic migrations
- 21 passing model tests

✅ **Phase 4**: REST API & Application Logic complete
- 28 API endpoints fully implemented
- Plant management (CRUD)
- Device management and registration
- Sensor data ingestion with device auth
- Watering decision engine with eligibility checks
- Virtual watering execution
- Alert service and endpoints
- Historical data and analytics APIs
- Comprehensive validation and error handling
- 21+ automated tests

**API Endpoints**: 28 total across all resources
**Services**: WateringService, AlertService
**Security**: Device-level authentication for sensors
**Documentation**: Complete API docs at `/docs`

⏳ **Phase 5**: User authentication, optimization

## Development

### Adding Dependencies

1. Add the package to `requirements.txt`
2. Update the virtual environment:
   ```bash
   pip install -r requirements.txt
   ```

### Adding New Endpoints

1. Create a new module in the `app/` directory or add to `app/main.py`
2. Define route handlers with appropriate type hints
3. Add corresponding tests in `tests/`
4. Run `pytest` to verify

## Support

See main project README for setup instructions and troubleshooting.
