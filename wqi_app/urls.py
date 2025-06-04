from django.urls import path
from . import views

# urls.py (remove the duplicate paths)
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('add-location/', views.add_location, name='add_location'),
    path('locations/', views.location_list, name='location_list'),
    path('locations/<int:pk>/', views.location_detail, name='location_detail'),
    path('locations/<int:pk>/measurements/', views.location_measurements, name='location_measurements'),
    path('add-measurement/', views.add_measurement, name='add_measurement'),
    path('measurement/<int:measurement_id>/', views.measurement_detail, name='measurement_detail'),
    path('map/', views.map_view, name='map_view'),
    path("export/excel/", views.export_measurements_to_excel, name="export_excel"),
    path("measurement/<int:id>/export/pdf/", views.export_measurements_to_pdf, name="export_pdf"),
    path('logout/', views.logout_view, name='logout'),
]