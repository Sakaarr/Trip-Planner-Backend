from django.db import models

class Trip(models.Model):
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_hours = models.FloatField(help_text="Total on-duty hours used in the current 70hr/8day cycle")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.current_location} ➜ {self.dropoff_location}"
