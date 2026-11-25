"""
Sensor simulator placeholder.

This module will simulate IoT sensor readings in Phase 3.

Planned features:
- Generate realistic sensor data (moisture, temperature, light)
- Support multiple plants
- Configurable data ranges and intervals
- API integration for sending readings to the backend
"""

from config import config


class SensorSimulator:
    """
    Simulates IoT sensor readings for plant monitoring.

    Placeholder for Phase 3 implementation.
    """

    def __init__(self):
        self.backend_url = config.BACKEND_URL
        self.plant_id = config.PLANT_ID
        self.sensor_interval = config.SENSOR_INTERVAL

    def generate_readings(self):
        """Generate simulated sensor readings."""
        raise NotImplementedError("Sensor simulation logic implemented in Phase 3")

    def send_to_backend(self, readings):
        """Send readings to the backend API."""
        raise NotImplementedError("API integration implemented in Phase 3")

    def start(self):
        """Start the simulator."""
        raise NotImplementedError("Simulator started in Phase 3")


if __name__ == "__main__":
    print("Sensor Simulator - Foundation Setup")
    print(f"Configured to connect to: {config.BACKEND_URL}")
    print(f"Plant ID: {config.PLANT_ID}")
    print(f"Sensor interval: {config.SENSOR_INTERVAL} seconds")
    print("\nCore simulation logic will be implemented in Phase 3")
