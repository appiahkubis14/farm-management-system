#!/usr/bin/env python3
"""
Test script to simulate ESP32 sensor sending data to the Django backend
"""

import requests
import json
import time
import random

# Configuration
SERVER_URL = "http://192.168.0.163:8000"
DEVICE_ID = "ESP32-TEST-001"
DEVICE_NAME = "Test Soil Sensor"
DEVICE_LOCATION = "Test Garden"

def register_device():
    """Register a test device"""
    url = f"{SERVER_URL}/api/register/"
    payload = {
        "device_id": DEVICE_ID,
        "device_name": DEVICE_NAME,
        "device_type": "multi",
        "location": DEVICE_LOCATION
    }
    
    print(f"Registering device: {DEVICE_ID}")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ Device registered successfully!")
            print(f"API Key: {data.get('api_key')}")
            return data.get('api_key')
        else:
            print(f"❌ Registration failed: {data.get('error')}")
            return None
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return None

def send_sensor_data(api_key, count=10):
    """Send simulated sensor data"""
    url = f"{SERVER_URL}/api/submit/"
    
    print(f"\n📡 Sending {count} sensor readings...")
    
    for i in range(count):
        # Generate realistic sensor data
        temperature = 20 + random.uniform(-5, 10)  # 15-30°C
        humidity = 50 + random.uniform(-20, 30)    # 30-80%
        soil_moisture = 40 + random.uniform(-15, 30)  # 25-70%
        battery_level = 85 + random.uniform(-5, 15)   # 80-100%
        signal_strength = -70 + random.randint(-20, 10)  # -90 to -60
        
        payload = {
            "device_id": DEVICE_ID,
            "api_key": api_key,
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "soil_moisture": round(soil_moisture, 1),
            "battery_level": round(battery_level, 1),
            "signal_strength": signal_strength
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Reading {i+1}/{count} sent - "
                      f"T:{payload['temperature']}°C "
                      f"H:{payload['humidity']}% "
                      f"S:{payload['soil_moisture']}%")
            else:
                print(f"❌ Failed to send reading {i+1}: {data.get('error')}")
        else:
            print(f"❌ HTTP Error {response.status_code}")
        
        # Wait between readings
        if i < count - 1:
            time.sleep(2)  # 2 seconds between readings

def main():
    """Main function"""
    print("🌱 IoT Sensor Test Script")
    print("=" * 50)
    
    # Register device
    api_key = register_device()
    
    if not api_key:
        print("\n❌ Could not register device. Make sure the server is running!")
        return
    
    # Send test data
    try:
        send_sensor_data(api_key, count=10)
        print("\n✅ Test completed successfully!")
        print(f"\n🌐 View the data at: {SERVER_URL}/")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
