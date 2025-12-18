from django.contrib import admin
from .models import Device, SensorReading


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'device_name', 'device_type', 'location', 'status', 'last_seen', 'registered_at')
    list_filter = ('device_type', 'status', 'registered_at')
    search_fields = ('device_id', 'device_name', 'location')
    readonly_fields = ('registered_at', 'last_seen', 'api_key')
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device_id', 'device_name', 'device_type', 'location', 'status')
        }),
        ('Security', {
            'fields': ('api_key',)
        }),
        ('Timestamps', {
            'fields': ('registered_at', 'last_seen')
        }),
    )


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('device', 'timestamp', 'temperature', 'humidity', 'soil_moisture', 'battery_level')
    list_filter = ('device', 'timestamp')
    search_fields = ('device__device_name', 'device__device_id')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Readings should only be added via API
        return False
