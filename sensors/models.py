from django.db import models
from django.utils import timezone
import uuid


class Device(models.Model):
    """Model to represent IoT devices (sensors)"""
    DEVICE_TYPES = [
        ('soil', 'Soil Moisture Sensor'),
        ('temperature', 'Temperature Sensor'),
        ('humidity', 'Humidity Sensor'),
        ('multi', 'Multi-Sensor Device'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
    ]
    
    device_id = models.CharField(max_length=100, unique=True, primary_key=True)
    device_name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES, default='multi')
    location = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    api_key = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-last_seen']
    
    def __str__(self):
        return f"{self.device_name} ({self.device_id})"


class SensorReading(models.Model):
    """Model to store sensor readings"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Sensor data fields
    temperature = models.FloatField(null=True, blank=True, help_text="Temperature in Celsius")
    humidity = models.FloatField(null=True, blank=True, help_text="Humidity percentage")
    soil_moisture = models.FloatField(null=True, blank=True, help_text="Soil moisture percentage")
    soil_raw = models.IntegerField(null=True, blank=True, help_text="Raw analog soil sensor value (0-4095)")
    
    # Additional metadata
    battery_level = models.FloatField(null=True, blank=True, help_text="Battery level percentage")
    signal_strength = models.IntegerField(null=True, blank=True, help_text="Signal strength")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['device', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.device_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def to_dict(self):
        """Convert reading to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'device_id': self.device.device_id,
            'device_name': self.device.device_name,
            'timestamp': self.timestamp.isoformat(),
            'temperature': self.temperature,
            'humidity': self.humidity,
            'soil_moisture': self.soil_moisture,
            'soil_raw': self.soil_raw,
            'battery_level': self.battery_level,
            'signal_strength': self.signal_strength,
        }
