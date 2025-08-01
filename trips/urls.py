from django.urls import path
from .views import TripViewSet

trip_create = TripViewSet.as_view({'post': 'create'})

urlpatterns = [
    path('trips/', trip_create, name='trip-create'),
]
