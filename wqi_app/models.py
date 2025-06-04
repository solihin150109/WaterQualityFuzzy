from django.db import models
from django.contrib.auth.models import User

class Location(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('location_detail', kwargs={'pk': self.id})

    @property
    def coordinates(self):
        """Helper property untuk koordinat"""
        return (float(self.latitude), float(self.longitude))
    
    def __str__(self):
        return f"{self.name} - {self.description}"

class WaterQualityMeasurement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    
    # WQI Parameters
    ph = models.FloatField()
    do = models.FloatField()
    bod = models.FloatField()
    cod = models.FloatField()
    total_coliform = models.FloatField()
    
    # WQI Results
    mamdani_wqi = models.FloatField(null=True, blank=True)
    mamdani_category = models.CharField(max_length=20, null=True, blank=True)
    sugeno_wqi = models.FloatField(null=True, blank=True)
    sugeno_category = models.CharField(max_length=20, null=True, blank=True)
    storet_wqi = models.FloatField(null=True, blank=True)
    storet_category = models.CharField(max_length=20, null=True, blank=True)
    storet_score = models.IntegerField(null=True, blank=True)
    storet_class = models.CharField(max_length=50, null=True, blank=True)
        
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Measurement at {self.location} on {self.date}"