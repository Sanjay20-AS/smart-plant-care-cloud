# Cloud-Connected Smart Plant Care & Watering System

## Project Description

A comprehensive IoT-enabled platform for monitoring and automating plant watering. The system consists of:

- **Sensor Simulator** (Python): Generates simulated sensor readings for plant conditions (moisture, temperature, light).
- **Backend** (Python FastAPI): REST API for sensor data ingestion, storage, and system control.
- **Frontend** (React): Real-time dashboard for monitoring plant health and watering status.
- **Database** (Supabase PostgreSQL): Persistent storage for sensor readings and system state.

## Approved Technology Stack

- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy
- **Frontend**: React (JavaScript), Recharts for visualization
- **Database**: Supabase PostgreSQL
- **Authentication**: Supabase Auth
- **Testing**: Pytest
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Version Control**: Git

## Project Structure

```
.
├── backend/              # FastAPI application
├── frontend/             # React application
├── sensor_simulator/     # Python sensor simulation
├── tests/                # Test suite
├── docs/                 # Architecture and documentation
├── .github/workflows/    # GitHub Actions workflows
├── docker/               # Docker configuration files
├── config/               # Environment and app configuration
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Prerequisites

- **Python 3.11+** (for backend and sensor simulator)
- **Node.js 18+** (for frontend)
- **Git**
- **Docker** (optional, for containerized development)

## Backend Setup

### Installation

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration values (see `.env.example` for placeholders).

### Running the Backend

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

Health check endpoint: `http://localhost:8000/health`

## Frontend Setup

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create a `.env` file in the `frontend/` directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration values.

### Running the Frontend

```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173` (default Vite port).

## Sensor Simulator Setup

### Configuration

Create a `.env` file in the `sensor_simulator/` directory:

```bash
cp .env.example .env
```

The simulator is not yet implemented. Configuration structure is in place for Phase 3.

## Environment Configuration

Each component has an `.env.example` template that documents required configuration variables. Copy these to `.env` files in the respective directories and populate with actual values.

**Important**: Never commit `.env` files. The `.gitignore` prevents accidental commits of credentials.

## Current Implementation Status

✅ **Phase 1**: Project structure created  
✅ **Phase 2**: Foundation dependencies and configuration prepared  
⏳ **Phase 3**: Core functionality (placeholder)  
⏳ **Phase 4**: Testing and optimization (placeholder)  
⏳ **Phase 5**: Deployment (placeholder)  

**Note**: Core functionality (database schema, API business logic, sensor simulation, dashboard features, authentication workflows) has not yet been implemented. This is a foundation setup only.

## Docker Support (Foundation)

Minimal Docker configurations are in place for local development. Full production containerization will be implemented in Phase 5.

## Testing

Pytest is configured for the backend. Run tests with:

```bash
cd backend
pytest
```

(Test suite is not yet implemented; this is configuration only.)

## Support and Documentation

- Architecture decisions and design documentation: See `docs/`
- Deployment guides: See GitHub Actions workflows in `.github/workflows/`
- Component-specific documentation: See component README files (forthcoming)

## License

[To be determined]

## Next Steps

The system is ready for Phase 3 implementation:
1. Database schema design and migrations
2. API endpoint implementation
3. Sensor simulator logic
4. Frontend dashboard and components
5. Authentication integration
