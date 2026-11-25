# Database Architecture & Implementation

## Overview

The Smart Plant Care system uses SQLAlchemy ORM with PostgreSQL for production (via Supabase) and SQLite for local development and testing. All schema management uses Alembic migrations.

## Database Configuration

### Environment Variables

Configure the database connection via environment variables in `backend/.env`:

```bash
# PostgreSQL (Production / Supabase)
DATABASE_URL=postgresql://user:password@host:5432/smartplant

# SQLite (Local Development - Default)
DATABASE_URL=sqlite:///./smartplant.db
```

**Default**: SQLite file-based database (`smartplant.db`)

### Supported Databases

- **PostgreSQL**: Production databases including Supabase
- **SQLite**: Local development and testing (in-memory and file-based)

### Configuration Details

**SQLite**:
- Local file: `smartplant.db`
- In-memory for testing
- Foreign key constraints enforced
- No external credentials required

**PostgreSQL**:
- Requires psycopg2-binary driver
- Full production support
- Supabase-compatible
- Connection pooling via SQLAlchemy

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────────┐
│     Plants      │
│─────────────────│
│ id (PK)         │
│ name            │
│ species         │
│ moisture_min    │
│ moisture_max    │
│ is_active       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1:N
         ├─────────────────────────┬─────────────────────────┬──────────────────┐
         │                         │                         │                  │
    ┌────▼──────────────┐  ┌─────▼─────────────┐  ┌────────▼────────┐  ┌────▼──────────┐
    │     Devices       │  │ SensorReadings    │  │WateringEvents   │  │    Alerts      │
    ├──────────────────┤  ├──────────────────┤  ├─────────────────┤  ├────────────────┤
    │ id (PK)          │  │ id (PK)          │  │ id (PK)        │  │ id (PK)        │
    │ device_id (UQ)   │  │ device_id (FK)   │  │ plant_id (FK)  │  │ plant_id (FK)  │
    │ plant_id (FK)    │  │ plant_id (FK)    │  │ device_id (FK) │  │ device_id (FK) │
    │ status           │  │ soil_moisture    │  │ duration_sec   │  │ alert_type     │
    │ last_seen        │  │ temperature      │  │ trigger_reason │  │ severity       │
    │ created_at       │  │ humidity         │  │ status         │  │ message        │
    │ updated_at       │  │ reading_ts       │  │ event_ts       │  │ status         │
    │                  │  │                  │  │                │  │ created_at     │
    │                  │  │                  │  │                │  │ resolved_at    │
    └──────────────────┘  └──────────────────┘  └────────────────┘  └────────────────┘
```

## Table Specifications

### Plants

Represents individual plants being monitored and managed.

**Columns:**
| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | Integer | PK | Primary key |
| name | String(255) | NOT NULL | Plant name |
| species | String(255) | NULLABLE | Plant species/type |
| moisture_threshold_min | Float | DEFAULT 30.0, CHECK (0-100) | Minimum safe moisture % |
| moisture_threshold_max | Float | DEFAULT 80.0, CHECK (0-100) | Maximum safe moisture % |
| is_active | Boolean | DEFAULT TRUE | Active status for filtering |
| created_at | DateTime | NOT NULL, DEFAULT now | Record creation time |
| updated_at | DateTime | NOT NULL, DEFAULT now | Last modification time |

**Indexes:**
- `idx_plant_active`: On `is_active` for quick filtering of active plants

**Constraints:**
- CHECK: `moisture_threshold_min >= 0 AND moisture_threshold_min <= 100`
- CHECK: `moisture_threshold_max >= 0 AND moisture_threshold_max <= 100`
- CHECK: `moisture_threshold_min <= moisture_threshold_max`

---

### Devices

Represents virtual IoT devices (sensors) associated with plants.

**Columns:**
| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | Integer | PK | Primary key |
| device_id | String(100) | NOT NULL, UNIQUE | External device identifier |
| plant_id | Integer | FK → Plants.id, ON DELETE CASCADE | Associated plant |
| status | String(50) | DEFAULT 'active' | Device status (active, inactive, error) |
| last_seen | DateTime | NULLABLE | Last communication timestamp |
| created_at | DateTime | NOT NULL, DEFAULT now | Record creation time |
| updated_at | DateTime | NOT NULL, DEFAULT now | Last modification time |

**Indexes:**
- `idx_device_plant_id`: On `plant_id` for plant-to-device queries
- `idx_device_status`: On `status` for filtering by device status
- `uq_device_id`: UNIQUE on `device_id` for external reference

**Relationships:**
- Many-to-One with Plants (cascade delete)
- One-to-Many with SensorReadings
- One-to-Many with WateringEvents
- One-to-Many with Alerts

---

### Sensor Readings

Stores historical sensor measurements from devices.

**Columns:**
| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | Integer | PK | Primary key |
| device_id | Integer | FK → Devices.id, NOT NULL, ON DELETE CASCADE | Associated device |
| plant_id | Integer | FK → Plants.id, NOT NULL, ON DELETE CASCADE | Associated plant |
| soil_moisture | Float | NOT NULL, CHECK (0-100) | Soil moisture percentage |
| temperature | Float | NULLABLE, in Celsius | Environmental temperature |
| humidity | Float | NULLABLE, CHECK (0-100) | Relative humidity percentage |
| reading_timestamp | DateTime | NOT NULL, DEFAULT now | Measurement timestamp |

**Indexes:**
- `idx_sensor_device_timestamp`: Composite on `(device_id, reading_timestamp)` for time-series queries
- `idx_sensor_plant_timestamp`: Composite on `(plant_id, reading_timestamp)` for plant history
- Auto-index on `reading_timestamp` for temporal queries

**Relationships:**
- Many-to-One with Devices (cascade delete)
- Many-to-One with Plants (cascade delete)

**Purpose:**
- Historical data storage for analytics and dashboards
- Time-series queries for trending
- Device health monitoring

---

### Watering Events

Records all watering activities and decisions.

**Columns:**
| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | Integer | PK | Primary key |
| plant_id | Integer | FK → Plants.id, NOT NULL, ON DELETE CASCADE | Associated plant |
| device_id | Integer | FK → Devices.id, NULLABLE, ON DELETE SET NULL | Associated device (optional) |
| duration_seconds | Integer | NULLABLE, CHECK >= 0 | Watering duration |
| trigger_reason | String(100) | NOT NULL | manual, automatic, scheduled, threshold |
| status | String(50) | DEFAULT 'completed' | completed, failed, cancelled |
| event_timestamp | DateTime | NOT NULL, DEFAULT now | Event timestamp |

**Indexes:**
- `idx_watering_plant_timestamp`: Composite on `(plant_id, event_timestamp)`
- `idx_watering_device_timestamp`: Composite on `(device_id, event_timestamp)`

**Relationships:**
- Many-to-One with Plants (cascade delete)
- Many-to-One with Devices (SET NULL on delete)

**Purpose:**
- Audit trail of watering decisions
- Support for manual and automated watering
- Historical analysis of plant care

---

### Alerts

Stores system alerts for plants and devices.

**Columns:**
| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | Integer | PK | Primary key |
| plant_id | Integer | FK → Plants.id, NULLABLE, ON DELETE CASCADE | Associated plant (optional) |
| device_id | Integer | FK → Devices.id, NULLABLE, ON DELETE CASCADE | Associated device (optional) |
| alert_type | String(100) | NOT NULL | dry, wet, low_battery, offline, error, etc. |
| severity | String(50) | NOT NULL | info, warning, critical |
| message | Text | NOT NULL | Alert description |
| status | String(50) | DEFAULT 'active' | active, acknowledged, resolved |
| created_at | DateTime | NOT NULL, DEFAULT now | Alert creation time |
| resolved_at | DateTime | NULLABLE | Resolution timestamp |

**Indexes:**
- `idx_alert_plant_created`: Composite on `(plant_id, created_at)`
- `idx_alert_device_created`: Composite on `(device_id, created_at)`
- `idx_alert_status`: On `status` for active alert queries

**Relationships:**
- Many-to-One with Plants (cascade delete, optional)
- Many-to-One with Devices (cascade delete, optional)

**Purpose:**
- Alert tracking and notifications
- Support for multi-level severity
- Status tracking for alert resolution workflows

---

## Database Relationships & Integrity

### Foreign Keys

All foreign keys enforce **referential integrity**:

| Relationship | On Delete |
|--------------|-----------|
| Device → Plant | CASCADE |
| SensorReading → Device | CASCADE |
| SensorReading → Plant | CASCADE |
| WateringEvent → Plant | CASCADE |
| WateringEvent → Device | SET NULL |
| Alert → Plant | CASCADE |
| Alert → Device | CASCADE |

### Cascading Deletes

**When a plant is deleted:**
- All associated devices are deleted
- All sensor readings are deleted
- All watering events are deleted
- All plant-associated alerts are deleted

**When a device is deleted:**
- Associated sensor readings are deleted
- Associated device-specific alerts are deleted
- Watering events keep plant_id but device_id becomes NULL

### Timestamps

All tables include automatic timestamp management:

- `created_at`: Set on record creation, never modified
- `updated_at`: Set on creation, updated on record modification

### Constraints Enforced

**Data Validation:**
- Moisture percentages: 0-100% range checked
- Humidity: 0-100% range checked
- Moisture thresholds: min ≤ max
- Duration: Non-negative integers

**Uniqueness:**
- `device_id`: Globally unique across all devices

## Migrations

### Setup Alembic

Alembic is configured in `backend/migrations/` for schema version control.

**Configuration files:**
- `alembic.ini`: Alembic configuration
- `env.py`: Migration environment with model import
- `script.py.mako`: Migration template

### Create Initial Database

```bash
cd backend

# Apply all pending migrations
alembic upgrade head
```

### Generate New Migrations

After modifying models in `app/models.py`:

```bash
cd backend

# Generate migration script automatically
alembic revision --autogenerate -m "description of change"

# Review the generated migration in migrations/versions/

# Apply the migration
alembic upgrade head
```

### Migration History

```bash
cd backend

# Show migration history
alembic history --verbose

# Show current database version
alembic current
```

### Downgrade Migrations

```bash
cd backend

# Downgrade to specific revision
alembic downgrade <revision_id>

# Downgrade one step
alembic downgrade -1
```

## Database Access

### Python ORM Interface

**Using the database module:**

```python
from app.database import SessionLocal, get_db, engine
from app.models import Plant, Device

# Using context manager
with SessionLocal() as db:
    plants = db.query(Plant).all()
    
# Using dependency injection (FastAPI)
from fastapi import Depends
from app.database import get_db
from sqlalchemy.orm import Session

@app.get("/plants/")
def list_plants(db: Session = Depends(get_db)):
    return db.query(Plant).all()
```

### Database Initialization

```python
from app.database import init_db

# Create all tables (use migrations in production)
init_db()
```

## Testing

### Test Database

Tests use an **in-memory SQLite database** isolated per test:

```python
# conftest.py provides fixtures
db_session  # Injected SQLAlchemy session
db_engine   # Injected engine
```

### Run Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run only database tests
pytest tests/test_models.py -v

# Run with coverage
pytest tests/test_models.py --cov=app
```

## Local Development Setup

### SQLite (Default)

No additional setup required. Database auto-creates on first run.

```bash
cd backend

# Apply migrations
alembic upgrade head

# Database file created: smartplant.db
```

### PostgreSQL (Alternative)

For testing with PostgreSQL locally:

```bash
# Install PostgreSQL locally (or use Docker)
# Create database
createdb smartplant

# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/smartplant

# Apply migrations
alembic upgrade head
```

## Production Deployment

### Supabase PostgreSQL

For cloud deployment with Supabase:

1. Create Supabase project
2. Get connection string from project settings
3. Set `DATABASE_URL` environment variable:

```bash
DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]
```

4. Apply migrations:

```bash
alembic upgrade head
```

5. Enable SSL for production connections

## Security Considerations

- **Credentials**: Database URLs are environment variables, never hardcoded
- **Migrations**: Alembic tracks schema changes for reproducibility
- **Foreign Keys**: Enforced at database level
- **SQL Injection**: SQLAlchemy ORM prevents SQL injection via parameterized queries
- **Connection Pooling**: Built-in SQLAlchemy pooling manages connections efficiently

## Schema Evolution

### Modifying Tables

1. **Update model** in `app/models.py`
2. **Generate migration**: `alembic revision --autogenerate -m "description"`
3. **Review migration** script in `migrations/versions/`
4. **Apply migration**: `alembic upgrade head`

### Best Practices

- Always use migrations for production changes
- Test migrations locally before production
- Keep migrations atomic and reversible
- Document significant schema changes in migration docstrings

## References

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Supabase PostgreSQL](https://supabase.com/docs/guides/database)
