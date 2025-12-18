from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/dashboard/$', consumers.DashboardConsumer.as_asgi()),
    re_path(r'ws/device/(?P<device_id>\w+)/$', consumers.SensorConsumer.as_asgi()),
]
