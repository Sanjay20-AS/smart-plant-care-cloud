"""
Sensor simulator configuration.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class SensorConfig:
    """Sensor simulator configuration."""

    # Backend API
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")

    # Sensor configuration
    SENSOR_INTERVAL = int(os.getenv("SENSOR_INTERVAL", "60"))
    PLANT_ID = os.getenv("PLANT_ID", "plant_001")
    DEVICE_ID = os.getenv("DEVICE_ID", None)  # Optional: defaults to sensor_{PLANT_ID}

    # Simulation parameters
    MOISTURE_MIN = int(os.getenv("MOISTURE_MIN", "20"))
    MOISTURE_MAX = int(os.getenv("MOISTURE_MAX", "80"))
    TEMPERATURE_MIN = int(os.getenv("TEMPERATURE_MIN", "15"))
    TEMPERATURE_MAX = int(os.getenv("TEMPERATURE_MAX", "35"))
    LIGHT_MIN = int(os.getenv("LIGHT_MIN", "0"))
    LIGHT_MAX = int(os.getenv("LIGHT_MAX", "100"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = SensorConfig()
