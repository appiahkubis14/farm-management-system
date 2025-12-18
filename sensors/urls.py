from django.urls import path
from . import views

app_name = 'sensors'

urlpatterns = [
    # Web views
    path('', views.dashboard, name='dashboard'),
    path('devices/', views.devices_list, name='devices_list'),
    path('device/<str:device_id>/', views.device_detail, name='device_detail'),
    path('test/', views.websocket_test, name='websocket_test'),
    
    # API endpoints
    path('api/register/', views.register_device, name='api_register_device'),
    path('api/submit/', views.submit_reading, name='api_submit_reading'),
    path('api/devices/', views.api_all_devices, name='api_all_devices'),
    path('api/device/<str:device_id>/readings/', views.api_device_readings, name='api_device_readings'),
    path('api/device/<str:device_id>/stats/', views.api_device_stats, name='api_device_stats'),
]
