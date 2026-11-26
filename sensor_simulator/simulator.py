"""
Sensor simulator for plant monitoring system.

Generates realistic sensor data and sends it to the backend API.
Supports multiple plants with configurable data ranges and intervals.
"""

import requests
import time
import random
import logging
from datetime import datetime
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SensorSimulator:
    """
    Simulates IoT sensor readings for plant monitoring.
    
    Generates realistic plant sensor data including:
    - Soil moisture (0-100%)
    - Temperature (-10 to +40°C)
    - Humidity (20-100%)
    
    Sends data to backend API endpoint.
    """

    def __init__(self):
        self.backend_url = config.BACKEND_URL
        self.plant_id = config.PLANT_ID
        self.sensor_interval = config.SENSOR_INTERVAL
        # Use DEVICE_ID from config if set, otherwise generate from PLANT_ID
        self.device_id = config.DEVICE_ID or f"sensor_{self.plant_id}"
        self.running = False
        
        # Sensor data ranges from config
        self.moisture_min = config.MOISTURE_MIN
        self.moisture_max = config.MOISTURE_MAX
        self.temperature_min = config.TEMPERATURE_MIN
        self.temperature_max = config.TEMPERATURE_MAX
        self.humidity_min = 20  # Minimum safe humidity
        self.humidity_max = 100  # Maximum safe humidity
        
        # Calculate base values as midpoints
        self.moisture_base = (self.moisture_min + self.moisture_max) / 2
        self.temperature_base = (self.temperature_min + self.temperature_max) / 2
        self.humidity_base = (self.humidity_min + self.humidity_max) / 2
        
        # Variation ranges (10% of the range)
        self.moisture_variation = (self.moisture_max - self.moisture_min) / 10
        self.temperature_variation = (self.temperature_max - self.temperature_min) / 10
        self.humidity_variation = (self.humidity_max - self.humidity_min) / 10

    def generate_readings(self):
        """Generate simulated sensor readings with realistic variation."""
        # Add random walk to simulate gradual changes
        moisture = max(self.moisture_min, min(self.moisture_max, 
            self.moisture_base + random.gauss(0, self.moisture_variation/2)
        ))
        
        temperature = self.temperature_base + random.gauss(0, self.temperature_variation/2)
        
        humidity = max(self.humidity_min, min(self.humidity_max, 
            self.humidity_base + random.gauss(0, self.humidity_variation/2)
        ))
        
        return {
            "device_id": self.device_id,
            "soil_moisture": round(moisture, 1),
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def send_to_backend(self, reading):
        """Send sensor reading to backend API."""
        endpoint = f"{self.backend_url}/sensor-readings"
        
        try:
            response = requests.post(
                endpoint,
                json=reading,
                timeout=5
            )
            response.raise_for_status()
            
            logger.info(
                f"✓ Sent reading | Moisture: {reading['soil_moisture']}% | "
                f"Temp: {reading['temperature']}°C | Humidity: {reading['humidity']}%"
            )
            return True
            
        except requests.exceptions.ConnectionError:
            logger.error(f"✗ Connection failed: Backend not reachable at {self.backend_url}")
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"✗ HTTP error: {e.response.status_code} - {e.response.text}")
            return False
        except requests.exceptions.Timeout:
            logger.error(f"✗ Request timeout")
            return False
        except Exception as e:
            logger.error(f"✗ Unexpected error: {str(e)}")
            return False

    def simulate_moisture_drop(self):
        """Simulate gradual moisture reduction (plant drying out)."""
        self.moisture_base = max(10, self.moisture_base - random.uniform(0.5, 2))

    def simulate_moisture_rise(self):
        """Simulate moisture increase (after watering)."""
        self.moisture_base = min(90, self.moisture_base + random.uniform(10, 20))

    def start(self):
        """Start the simulator - continuously sends sensor readings."""
        self.running = True
        logger.info(f"Starting sensor simulator for device: {self.device_id}")
        logger.info(f"Sending readings every {self.sensor_interval} seconds")
        logger.info(f"Backend: {self.backend_url}")
        logger.info("=" * 60)
        
        read_count = 0
        
        try:
            while self.running:
                # Generate and send reading
                reading = self.generate_readings()
                self.send_to_backend(reading)
                
                read_count += 1
                
                # Simulate moisture gradually dropping (plant needs water)
                if read_count % 5 == 0:  # Every 5 readings
                    self.simulate_moisture_drop()
                
                time.sleep(self.sensor_interval)
                
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("Simulator stopped by user")
            self.running = False


if __name__ == "__main__":
    simulator = SensorSimulator()
    
    print("=" * 60)
    print("Smart Plant Care - Sensor Simulator")
    print("=" * 60)
    print(f"Backend URL: {simulator.backend_url}")
    print(f"Device ID: {simulator.device_id}")
    print(f"Sensor Interval: {simulator.sensor_interval} seconds")
    print("=" * 60)
    print("Starting sensor readings...\n")
    
    simulator.start()

