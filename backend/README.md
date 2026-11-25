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
│   └── main.py          # FastAPI application entry point
├── tests/
│   ├── __init__.py
│   └── test_health.py   # Health check tests
├── config.py            # Pydantic settings
├── requirements.txt     # Python dependencies
├── .env.example         # Configuration template
└── pytest.ini           # Pytest configuration
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app tests/
```

## API Documentation

Once the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Configuration

All configuration is managed through environment variables in the `.env` file.

**Key variables:**
- `BACKEND_URL` / `DATABASE_URL` - Database connection
- `SUPABASE_URL` / `SUPABASE_KEY` - Supabase credentials
- `DEBUG` - Enable debug mode
- `LOG_LEVEL` - Logging verbosity

## Implementation Status

✅ **Phase 2**: Foundation setup complete
- FastAPI application initialized
- Configuration system (Pydantic settings)
- Health check endpoint
- Test framework configured

⏳ **Phase 3**: Core functionality
- Database schema and migrations
- API business endpoints
- Authentication and authorization
- Sensor data models

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
