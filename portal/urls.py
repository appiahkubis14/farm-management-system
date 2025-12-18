from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from portal.view.farms import *
from portal.view.map import *

urlpatterns = [
    path('home/', views.index, name='home'),
    path('', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('change-password/', views.change_password, name='change_password'),
    path('password-change-done/', views.password_change_done, name='password_change_done'),


    # Main page
    path('farm-management/farms/', farm_details_page, name='farm_details_page'),
    
    # API endpoints
    path('api/farm-details/', farm_details_api, name='farm_details_api'),
    path('api/farm-details/<int:farm_id>/', get_farm_details, name='get_farm_details'),
    path('api/farm-details/create/', create_farm, name='create_farm'),
    path('api/farm-details/<int:farm_id>/update/', update_farm, name='update_farm'),
    path('api/farm-details/<int:farm_id>/delete/', delete_farm, name='delete_farm'),
    path('api/get-districts-by-region/', get_districts_by_region, name='get_districts_by_region'),

     path('farm-management/mapped-farms/', farm_mapping_page, name='farm_mapping_page'),
    path('api/farm-geojson/', get_farm_geojson, name='get_farm_geojson'),
    path('api/district-boundaries/', get_district_boundaries, name='get_district_boundaries'),
    path('api/farm-stats/', get_farm_stats, name='get_farm_stats'),
    path('api/search-farms/', search_farms, name='search_farms'),
    path('api/farm/<int:farm_id>/', get_farm_by_id, name='get_farm_by_id'),
]