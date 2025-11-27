# home/models.py
from django.db import models

class Slider(models.Model):
    name = models.CharField(max_length=100, default="Slide")
    image = models.ImageField(upload_to='sliders')
    description = models.TextField(blank=True, null=True) # Dòng chữ trên ảnh (nếu cần)
    
    def __str__(self):
        return self.name