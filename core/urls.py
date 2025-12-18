from django.urls import path

from core.models import SidebarMenu



urlpatterns = [
    path('SidebarMenu/', SidebarMenu),
    # path('tracking-dashboard/', tracking_view, name='tracking_dashboard'),
    # path('reports/', report, name='report'),
    # path('fetch-report-data/', fetch_report_data, name='fetch_report_data'),
    # # path('login-history/', login_history_view, name='login-history'),
]

