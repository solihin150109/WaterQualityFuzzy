from django.contrib import admin
from .models import Location, WaterQualityMeasurement

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)

@admin.register(WaterQualityMeasurement)
class WaterQualityMeasurementAdmin(admin.ModelAdmin):
    list_display = ('location', 'date', 'user', 'do', 'ph', 'bod', 'cod', 'total_coliform', 'storet_score', 'mamdani_wqi', 'sugeno_wqi')
    list_filter = ('location', 'date', 'user')
    search_fields = ('location__name', 'user__username')