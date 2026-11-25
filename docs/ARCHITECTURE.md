# Architecture Overview

## System Components

### 1. Sensor Simulator (Python)
- Generates simulated IoT sensor readings
- Readings include: soil moisture, temperature, light levels
- Runs as a standalone service or scheduled task
- Publishes readings to the backend API

### 2. Backend (FastAPI)
- RESTful API for all operations
- Receives and stores sensor readings
- Provides data access endpoints for the frontend
- Manages user sessions and application state
- Database interface layer via SQLAlchemy

### 3. Frontend (React)
- Real-time dashboard displaying plant status
- Visualizations powered by Recharts
- User authentication via Supabase Auth
- Responsive design for desktop and mobile

### 4. Database (Supabase PostgreSQL)
- Persistent storage for sensor readings
- User accounts and authentication data
- System configuration and metadata
- Time-series data for historical analysis

## Data Flow

1. **Sensor Simulator** → generates simulated readings
2. **Backend API** ← receives readings via POST request
3. **Database** ← readings stored via SQLAlchemy ORM
4. **Frontend** ← polls/subscrioes to API for real-time updates
5. **User Dashboard** ← displays charts, alerts, and status

## API Design (REST)

- Base URL: `{BACKEND_URL}/api/v1`
- Authentication: Bearer token (Supabase JWT)
- Response format: JSON
- Status codes: Standard HTTP semantics

Endpoints to be implemented in Phase 3.

## Technology Decisions

### Why FastAPI?
- High performance, modern Python framework
- Built-in OpenAPI documentation
- Strong async support for I/O-bound operations
- Excellent type safety with Pydantic

### Why React?
- Efficient UI updates with virtual DOM
- Large ecosystem and community support
- Excellent developer experience
- Well-suited for real-time dashboards

### Why Supabase?
- Managed PostgreSQL database
- Built-in authentication (PostgREST, Auth)
- Real-time capabilities
- Cost-effective for small to mid-scale applications
- No additional infrastructure management required

### Why Docker?
- Consistent development and deployment environments
- Simplified dependency management
- Production-ready containerization

## Scalability Considerations

Future phases may include:
- Message queue (e.g., RabbitMQ, Kafka) for high-volume sensor data
- Caching layer (Redis) for frequently accessed data
- Microservices decomposition as complexity grows
- Dedicated analytics pipeline for historical data

## Security Considerations

- API authentication via Supabase JWT tokens
- HTTPS enforced in production
- Environment variables for sensitive configuration
- Secrets excluded from version control
- SQL injection prevention via parameterized queries (SQLAlchemy)
- CORS configuration for frontend access

## Development vs. Production

**Development**:
- FastAPI with hot reload
- SQLite (optional) or local Supabase instance for testing
- Mock sensor data

**Production**:
- FastAPI behind a production ASGI server (Uvicorn, Gunicorn)
- Supabase managed PostgreSQL
- Real sensor data
- Comprehensive logging and monitoring

## Deployment Architecture (Future)

- Backend: Containerized on cloud platform (AWS ECS, Google Cloud Run, Azure Container Instances)
- Frontend: Static hosting (AWS S3 + CloudFront, Vercel, Netlify)
- Database: Managed Supabase instance
- CI/CD: GitHub Actions for automated testing and deployment
