from rest_framework import serializers
from .models import Trip

class TripInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['id', 'current_location', 'pickup_location', 'dropoff_location', 'current_cycle_hours']
        read_only_fields = ['id']
