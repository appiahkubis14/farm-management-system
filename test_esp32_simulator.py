#!/usr/bin/env python3
"""
ESP32 Data Simulator - Sends test data to Django backend
Use this to test if your server is receiving and processing data correctly
"""

import requests
import json
import time
import random

SERVER_URL = "http://192.168.0.152:8008"
DEVICE_ID = "ESP32-001"
DEVICE_NAME = "Soil Sensor 1"
DEVICE_LOCATION = "Garden A"

def register_device():
    """Register device with the server"""
    url = f"{SERVER_URL}/api/register/"
    data = {
        "device_id": DEVICE_ID,
        "device_name": DEVICE_NAME,
        "device_type": "multi",
        "location": DEVICE_LOCATION
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Registration Response: {response.status_code}")
        print(response.json())
        return response.json().get('api_key', '')
    except Exception as e:
        print(f"Registration Error: {e}")
        return None

def send_sensor_data(api_key):
    """Send simulated sensor data"""
    url = f"{SERVER_URL}/api/submit/"
    
    # Simulate realistic sensor readings
    temp = round(20 + random.uniform(-5, 15), 1)  # 15-35°C
    humidity = round(40 + random.uniform(0, 40), 1)  # 40-80%
    soil_percent = random.randint(30, 80)  # 30-80%
    soil_raw = int(4095 - (soil_percent / 100) * 2595)  # Convert % to raw (4095-1500 range)
    
    data = {
        "device_id": DEVICE_ID,
        "api_key": api_key,
        "temperature": temp,
        "humidity": humidity,
        "soil_moisture": soil_percent,
        "soil_raw": soil_raw,
        "battery_level": 100.0,
        "signal_strength": random.randint(15, 31)
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"\n📡 Sending Data at {time.strftime('%H:%M:%S')}")
        print(f"   🌡️  Temp: {temp}°C")
        print(f"   💧 Humidity: {humidity}%")
        print(f"   🌱 Soil: {soil_percent}%")
        print(f"   📊 Raw: {soil_raw}")
        print(f"   ✅ Response: {response.status_code}")
        if response.status_code == 200:
            print(f"   {response.json()}")
        else:
            print(f"   Error: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Send Error: {e}")
        return False

def main():
    print("=" * 60)
    print("ESP32 Data Simulator")
    print("=" * 60)
    print(f"Server: {SERVER_URL}")
    print(f"Device: {DEVICE_ID}")
    print("=" * 60)
    
    # Register device first
    print("\n🔐 Registering device...")
    api_key = register_device()
    
    if not api_key:
        print("❌ Failed to register device. Exiting.")
        return
    
    print(f"✅ Device registered! API Key: {api_key}")
    print("\n📡 Starting to send sensor data every 5 seconds...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            send_sensor_data(api_key)
            time.sleep(5)  # Send every 5 seconds
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")

if __name__ == "__main__":
    main()
