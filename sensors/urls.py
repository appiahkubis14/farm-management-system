from django.urls import path
from . import views

app_name = 'sensors'

urlpatterns = [
    # Web views
    path('dashboard/', views.dashboard, name='dashboard'),
     path('api/dashboard-stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('devices/', views.devices_list, name='devices_list'),
    path('device/<str:device_id>/', views.device_detail, name='device_detail'),
    path('test/', views.websocket_test, name='websocket_test'),
    
    # API endpoints
    path('api/register/', views.register_device, name='api_register_device'),
    path('api/submit/', views.submit_reading, name='api_submit_reading'),
    path('api/devices/', views.api_all_devices, name='api_all_devices'),
    path('api/device/<str:device_id>/readings/', views.api_device_readings, name='api_device_readings'),
    path('api/device/<str:device_id>/stats/', views.api_device_stats, name='api_device_stats'),

    # Device management
    path('devices/management/', views.devices_management, name='devices_management'),
    path('api/devices/list/', views.api_devices_list, name='api_devices_list'),
    path('api/devices/create/', views.api_device_create, name='api_device_create'),
    path('api/devices/<str:device_id>/', views.api_device_detail, name='api_device_detail'),
    path('api/devices/<str:device_id>/update/', views.api_device_update, name='api_device_update'),
    path('api/devices/<str:device_id>/delete/', views.api_device_delete, name='api_device_delete'),
    path('api/devices/<str:device_id>/generate-key/', views.api_device_generate_key, name='api_device_generate_key'),


    
]
