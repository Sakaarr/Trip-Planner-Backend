from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import Trip
from .serializers import TripInputSerializer
from .utils import get_route_distance
from shapely.geometry import LineString
import polyline

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

            # --- Route Calculation ---
            dist1, coords1 = get_route_distance(trip.current_location, trip.pickup_location)
            dist2, coords2 = get_route_distance(trip.pickup_location, trip.dropoff_location)

            segment1 = polyline.decode(coords1["geometry_encoded"])  # [[lat, lon], ...]
            segment2 = polyline.decode(coords2["geometry_encoded"])
            full_route = segment1 + segment2
            full_encoded_route = polyline.encode(full_route)

            total_distance = (dist1 or 0) + (dist2 or 0)
            driving_speed = 50.0
            driving_hours = total_distance / driving_speed
            pickup_drop_time = 2  # 1h pickup + 1h dropoff
            fuel_stops = int(total_distance // 1000)
            fuel_time = fuel_stops * 0.25
            total_hours = fuel_time + driving_hours + pickup_drop_time

            # --- Log Sheet Generation ---
            logs = []
            hours_left = total_hours
            day = 1
            cycle_hours = trip.current_cycle_hours

            while hours_left > 0:
                if cycle_hours >= 70:
                    logs.append({
                        "day": day,
                        "driving_hours": 0,
                        "other_duty": 0,
                        "rest": 34.0,  # Simulated reset
                        "note": "34-hour reset"
                    })
                    cycle_hours = 0
                    day += 1
                    continue

                max_available_today = min(14, 70 - cycle_hours)
                driving = min(11, hours_left, max_available_today)

                break_time = 0.5 if driving > 8 else 0
                other_duty = min(3 - break_time, hours_left - driving) if hours_left - driving > 0 else 0

                day_log = {
                    "day": day,
                    "driving_hours": round(driving, 2),
                    "other_duty": round(other_duty + break_time, 2),
                    "rest": 10.0
                }
                logs.append(day_log)

                cycle_hours += driving + break_time + other_duty
                hours_left -= (driving + other_duty)
                day += 1
            # --- Fuel Stop Coordinates from Line Geometry ---
            full_coords = polyline.decode(full_encoded_route)
            line = LineString([(lon, lat) for lat, lon in full_coords])
            fuel_stop_coords = []

            if coords2 and fuel_stops > 0:
                for i in range(1, fuel_stops + 1):
                    point = line.interpolate(i / (fuel_stops + 1), normalized=True)
                    fuel_stop_coords.append([round(point.y, 6), round(point.x, 6)])

            # --- HOS Violation Detection ---
            hos_violation = False
            hos_message = ""
            projected_total_cycle = total_hours + trip.current_cycle_hours

            if trip.current_cycle_hours >= 70:
                hos_violation = True
                hos_message += "Driver has already exceeded the 70-hour limit before starting this trip. "

            if projected_total_cycle > 70:
                hos_violation = True
                excess = round(projected_total_cycle - 70, 2)
                hos_message += f"Trip exceeds 70-hour limit in 8-day cycle by {excess} hours. "

            for log in logs:
                total_day_hours = log["driving_hours"] + log["other_duty"]
                if log["driving_hours"] > 11:
                    hos_violation = True
                    hos_message += f"Day {log['day']} exceeds 11 hours of driving. "
                if total_day_hours > 14:
                    hos_violation = True
                    hos_message += f"Day {log['day']} exceeds 14-hour duty window. "

            # Partial log warning if trip could not be fully logged
            if hours_left > 0:
                hos_violation = True
                hos_message += f"Trip was only partially logged due to reaching the 70-hour cycle limit. " \
                               f"{round(hours_left, 2)} duty hours remain unallocated. "

            # --- Response Data ---
            response_data = {
                "from": trip.current_location,
                "pickup": trip.pickup_location,
                "to": trip.dropoff_location,
                "total_distance_miles": round(total_distance, 2),
                "estimated_days": len(logs),
                "fuel_stops": fuel_stops,
                "log_sheets": logs,
                "hos_violation": hos_violation,
                "hos_warning": hos_message if hos_violation else None,
                "actual_logged_hours": round(total_hours - hours_left, 2),
                "unallocated_hours": round(hours_left, 2) if hours_left > 0 else 0.0,
                "coordinates": {
                    "current_location": coords1.get("start"),
                    "pickup_location": coords1.get("end"),
                    "dropoff_location": coords2.get("end"),
                    "fuel_stop_coords": fuel_stop_coords,
                    "route_geometry_encoded": full_encoded_route,
                }
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        # If serializer is not valid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)