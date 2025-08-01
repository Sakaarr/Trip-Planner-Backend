from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import Trip
from .serializers import TripInputSerializer
from .utils import get_route_distance

class TripViewSet(viewsets.ViewSet):
    @extend_schema(
        request=TripInputSerializer,
        responses={200: dict},
        examples=[
            OpenApiExample(
                "Basic Trip Input",
                value={
                    "current_location": "Denver, CO",
                    "pickup_location": "Chicago, IL",
                    "dropoff_location": "Boston, MA",
                    "current_cycle_hours": 40.5
                }
            )
        ]
    )
    def create(self, request):
        serializer = TripInputSerializer(data=request.data)
        if serializer.is_valid():
            trip = serializer.save()

            dist1 = get_route_distance(trip.current_location, trip.pickup_location)
            dist2 = get_route_distance(trip.pickup_location, trip.dropoff_location)
            total_distance = (dist1 or 0) + (dist2 or 0)

            driving_hours = total_distance / 50
            total_hours = driving_hours + 2  # 1h pickup + 1h dropoff

            # Add fuel stop every 1000 miles
            fuel_stops = int(total_distance // 1000)
            fuel_time = fuel_stops * 0.25
            total_hours += fuel_time

            # Break into daily log sheets
            logs = []
            hours_left = total_hours
            day = 1

            while hours_left > 0:
                driving = min(11, hours_left)
                other_duty = min(3, hours_left - driving) if hours_left - driving > 0 else 0
                logs.append({
                    "day": day,
                    "driving_hours": round(driving, 2),
                    "other_duty": round(other_duty, 2),
                    "rest": 10.0
                })
                hours_left -= (driving + other_duty)
                day += 1
            print(get_route_distance("San Francisco, CA", "New York, NY"))
            return Response({
                "from": trip.current_location,
                "to": trip.dropoff_location,
                "total_distance_miles": round(total_distance, 2),
                "estimated_days": len(logs),
                "fuel_stops": fuel_stops,
                "log_sheets": logs
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)