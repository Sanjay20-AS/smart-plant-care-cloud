# Smart Plant Care API Documentation

## Overview

The Smart Plant Care API provides REST endpoints for managing plants, devices, sensor data, watering decisions, and system alerts. The API is built with FastAPI and uses a SQLAlchemy ORM for data persistence.

**Base URL**: `http://localhost:8000/api/v1`

**Documentation**: `http://localhost:8000/docs` (Swagger UI)

## Authentication & Security

### Current Stage (Phase 4)

Device-level authentication is implemented for sensor ingestion:
- **Sensor Ingestion**: Requires valid `device_id` from registered device
- **Device Management**: No authentication required (development stage)
- **Plant Management**: No authentication required (development stage)

### Future Integration (Phase 6)

User authentication will be integrated via Supabase Auth:
- JWT tokens will be required for user-facing endpoints
- Device API keys will be managed separately from user authentication
- Role-based access control will be implemented

**Warning**: The current API is NOT suitable for production without additional authentication layers.

---

## Core Concepts

### Plants

A plant represents an individual plant being monitored. Each plant has care thresholds that determine when watering is needed.

**Attributes**:
- `id`: Unique identifier
- `name`: Plant name
- `species`: Plant species (optional)
- `moisture_threshold_min`: Minimum soil moisture % for watering trigger (default: 30%)
- `moisture_threshold_max`: Maximum safe moisture % (default: 80%)
- `is_active`: Active status for filtering

### Devices

A device represents an IoT sensor associated with a plant. Each device has a unique `device_id` and status.

**Attributes**:
- `id`: Unique database identifier
- `device_id`: External device identifier (must be unique)
- `plant_id`: Associated plant ID
- `status`: active, inactive, or error
- `last_seen`: Last communication timestamp

### Sensor Readings

Historical sensor data from devices, including moisture, temperature, and humidity.

**Attributes**:
- `soil_moisture`: Soil moisture percentage (0-100%)
- `temperature`: Temperature in Celsius (optional)
- `humidity`: Relative humidity percentage (0-100%, optional)
- `reading_timestamp`: Measurement timestamp

### Watering Events

Records of watering operations or decisions.

**Attributes**:
- `plant_id`: Associated plant
- `device_id`: Associated device (optional)
- `duration_seconds`: Virtual watering duration
- `trigger_reason`: manual, automatic, scheduled, or threshold
- `status`: completed, failed, or cancelled
- `event_timestamp`: Event timestamp

### Alerts

System alerts for plants or devices.

**Attributes**:
- `alert_type`: dry, wet, low_battery, offline, error, etc.
- `severity`: info, warning, or critical
- `message`: Alert description
- `status`: active, acknowledged, or resolved
- `plant_id`: Associated plant (optional)
- `device_id`: Associated device (optional)

---

## API Endpoints

### Plants

#### Create Plant

```http
POST /api/v1/plants
Content-Type: application/json

{
  "name": "Tomato Plant",
  "species": "Solanum lycopersicum",
  "moisture_threshold_min": 30.0,
  "moisture_threshold_max": 80.0,
  "is_active": true
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "name": "Tomato Plant",
  "species": "Solanum lycopersicum",
  "moisture_threshold_min": 30.0,
  "moisture_threshold_max": 80.0,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### List Plants

```http
GET /api/v1/plants?skip=0&limit=100&active_only=false
```

**Query Parameters**:
- `skip`: Number of items to skip (default: 0)
- `limit`: Number of items to return (default: 100, max: 1000)
- `active_only`: Filter to active plants only (default: false)

#### Get Plant

```http
GET /api/v1/plants/{plant_id}
```

#### Update Plant

```http
PUT /api/v1/plants/{plant_id}
Content-Type: application/json

{
  "moisture_threshold_min": 25.0,
  "is_active": true
}
```

#### Delete Plant

```http
DELETE /api/v1/plants/{plant_id}
```

---

### Devices

#### Register Device

```http
POST /api/v1/devices
Content-Type: application/json

{
  "device_id": "sensor_001",
  "plant_id": 1,
  "status": "active"
}
```

#### List Devices

```http
GET /api/v1/devices?plant_id=1&status=active&skip=0&limit=100
```

**Query Parameters**:
- `plant_id`: Filter by plant ID (optional)
- `status`: Filter by device status (optional)
- `skip`: Offset (default: 0)
- `limit`: Limit (default: 100, max: 1000)

#### Get Device

```http
GET /api/v1/devices/{device_id}
```

#### Update Device

```http
PUT /api/v1/devices/{device_id}
Content-Type: application/json

{
  "status": "inactive",
  "plant_id": 1
}
```

#### Delete Device

```http
DELETE /api/v1/devices/{device_id}
```

---

### Sensor Data Ingestion

#### Ingest Sensor Reading

```http
POST /api/v1/sensor-readings
Content-Type: application/json

{
  "device_id": "sensor_001",
  "soil_moisture": 65.5,
  "temperature": 22.3,
  "humidity": 58.0,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Security**: Requires a registered active device with matching `device_id`

**Response** (201 Created):
```json
{
  "id": 1,
  "device_id": 1,
  "plant_id": 1,
  "soil_moisture": 65.5,
  "temperature": 22.3,
  "humidity": 58.0,
  "reading_timestamp": "2024-01-15T10:30:00Z"
}
```

#### Get Plant Sensor Readings

```http
GET /api/v1/sensor-readings/plant/{plant_id}?skip=0&limit=100&hours=24
```

**Query Parameters**:
- `skip`: Offset (default: 0)
- `limit`: Limit (default: 100, max: 1000)
- `hours`: Time range in hours (default: 24, max: 720)

#### Get Latest Plant Readings

```http
GET /api/v1/sensor-readings/latest/{plant_id}
```

**Response**:
```json
{
  "plant_id": 1,
  "latest_moisture": 65.5,
  "latest_temperature": 22.3,
  "latest_humidity": 58.0,
  "last_reading_timestamp": "2024-01-15T10:30:00Z",
  "reading_count": 150
}
```

---

### Watering

#### Evaluate Watering Decision

```http
POST /api/v1/watering/decision/{plant_id}?device_id=1
```

**Response**:
```json
{
  "eligible": true,
  "reason": "Watering eligible - moisture 20% below threshold 30%",
  "plant_id": 1,
  "device_id": 1,
  "current_moisture": 20.0,
  "moisture_threshold": 30.0,
  "decision_timestamp": "2024-01-15T10:30:00Z",
  "cooldown_remaining_minutes": null,
  "daily_limit_remaining": 3
}
```

#### Execute Virtual Watering

```http
POST /api/v1/watering/execute/{plant_id}?device_id=1
```

**Response** (201 Created):
```json
{
  "success": true,
  "event_id": 1,
  "duration_seconds": 120,
  "message": "Virtual watering completed for 120s",
  "decision": { ... }
}
```

#### Get Watering History

```http
GET /api/v1/watering/history/{plant_id}?skip=0&limit=100&days=30
```

#### Get Watering Summary

```http
GET /api/v1/watering/summary/{plant_id}
```

**Response**:
```json
{
  "plant_id": 1,
  "total_events": 25,
  "last_watering_timestamp": "2024-01-15T08:00:00Z",
  "recent_watering_count_24h": 1,
  "next_eligible_time": "2024-01-15T20:00:00Z"
}
```

---

### Alerts

#### List Alerts

```http
GET /api/v1/alerts?plant_id=1&status=active&severity=warning&skip=0&limit=100
```

**Query Parameters**:
- `plant_id`: Filter by plant (optional)
- `status`: Filter by status (optional)
- `severity`: Filter by severity (optional)
- `skip`: Offset (default: 0)
- `limit`: Limit (default: 100, max: 1000)

#### Get Alert

```http
GET /api/v1/alerts/{alert_id}
```

#### Update Alert Status

```http
PUT /api/v1/alerts/{alert_id}
Content-Type: application/json

{
  "status": "acknowledged"
}
```

---

### Analytics

#### Get Plant Analytics

```http
GET /api/v1/analytics/plant/{plant_id}
```

**Response**:
```json
{
  "plant_id": 1,
  "plant_name": "Tomato Plant",
  "latest_moisture": 65.5,
  "latest_temperature": 22.3,
  "latest_humidity": 58.0,
  "last_reading_timestamp": "2024-01-15T10:30:00Z",
  "reading_count": 150,
  "recent_readings_24h": 24,
  "device_count": 1,
  "active_devices": 1,
  "recent_watering_count": 1,
  "last_watering_timestamp": "2024-01-15T08:00:00Z",
  "alert_count_active": 1,
  "alert_count_critical": 0
}
```

#### Get System Summary

```http
GET /api/v1/analytics/summary
```

**Response**:
```json
{
  "total_plants": 5,
  "active_plants": 4,
  "total_devices": 8,
  "active_devices": 7,
  "total_readings": 2500,
  "total_watering_events": 50,
  "active_alerts": 3,
  "critical_alerts": 0
}
```

---

## Watering Decision Logic

The watering engine evaluates multiple criteria before determining if watering is eligible:

1. **Plant Validation**: Plant must exist and be active
2. **Device Validation**: Active device must be associated with the plant
3. **Sensor Data**: Recent reading required (< 60 minutes old)
4. **Moisture Threshold**: Soil moisture must be below `moisture_threshold_min`
5. **Cooldown Period**: 12-hour minimum between waterings
6. **Daily Limit**: Maximum 3 watering events per day

**Decision Response Includes**:
- `eligible`: Boolean eligibility status
- `reason`: Human-readable reason for decision
- `current_moisture`: Latest soil moisture reading
- `cooldown_remaining_minutes`: Time until next watering (if applicable)
- `daily_limit_remaining`: Remaining watering events for today

---

## Error Handling

### Status Codes

- `200 OK`: Successful GET request
- `201 Created`: Successful POST request with resource creation
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Device authentication failed
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": "Plant not found",
  "detail": "Plant with ID 999 does not exist",
  "status_code": 404
}
```

---

## Validation Rules

### Plant Thresholds
- `moisture_threshold_min`: 0-100%, must be ≤ `moisture_threshold_max`
- `moisture_threshold_max`: 0-100%, must be ≥ `moisture_threshold_min`

### Sensor Readings
- `soil_moisture`: 0-100% (required)
- `temperature`: -50 to +60°C (optional)
- `humidity`: 0-100% (optional)

### Device ID
- Must be unique across all devices
- String length: 1-100 characters

---

## Configuration

### Watering Engine Configuration

**Hardcoded (in services.py)**:
- `WATERING_COOLDOWN_HOURS = 12`: Minimum hours between waterings
- `MAX_WATERING_EVENTS_PER_DAY = 3`: Maximum daily watering events
- `SENSOR_DATA_FRESHNESS_MINUTES = 60`: Maximum age of sensor data
- `VIRTUAL_WATERING_DURATION_SECONDS = 120`: Simulated watering duration

These values can be moved to environment configuration in future phases.

---

## Example Usage

### Complete Workflow

```bash
# 1. Create a plant
curl -X POST http://localhost:8000/api/v1/plants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tomato",
    "moisture_threshold_min": 30,
    "moisture_threshold_max": 80
  }'

# 2. Register a device
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "sensor_001",
    "plant_id": 1,
    "status": "active"
  }'

# 3. Ingest sensor reading
curl -X POST http://localhost:8000/api/v1/sensor-readings \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "sensor_001",
    "soil_moisture": 25,
    "temperature": 22,
    "humidity": 60
  }'

# 4. Check watering eligibility
curl -X POST http://localhost:8000/api/v1/watering/decision/1

# 5. Execute watering if eligible
curl -X POST http://localhost:8000/api/v1/watering/execute/1

# 6. Get plant analytics
curl http://localhost:8000/api/v1/analytics/plant/1
```

---

## Testing

Run the backend test suite:

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_routes.py -v

# Run with coverage
pytest tests/ --cov=app
```

---

## Future Enhancements

1. **User Authentication**: Supabase Auth integration
2. **Role-Based Access**: Admin, user, device roles
3. **Device API Keys**: Secure device authentication tokens
4. **Webhooks**: Event notifications
5. **Real-time Updates**: WebSocket support
6. **Advanced Analytics**: Historical trends and predictions
7. **Scheduler**: Automated watering decisions
8. **Multi-user Support**: User-scoped data access

---

## Support

For issues or questions, refer to:
- API Swagger documentation: `http://localhost:8000/docs`
- Backend README: `docs/README.md`
- Database schema: `docs/DATABASE.md`
