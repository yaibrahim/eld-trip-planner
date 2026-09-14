from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from . import hos
from .geocode import GeocodeError, RoutingError
from .models import Trip
from .serializers import TripPlanRequestSerializer, TripSerializer


@api_view(["POST"])
def plan_trip(request):
    req = TripPlanRequestSerializer(data=request.data)
    req.is_valid(raise_exception=True)
    data = req.validated_data

    try:
        result = hos.plan_trip(
            data["current_location"],
            data["pickup_location"],
            data["dropoff_location"],
            data["current_cycle_used"],
        )
    except (GeocodeError, RoutingError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    trip = Trip.objects.create(
        current_location=data["current_location"],
        pickup_location=data["pickup_location"],
        dropoff_location=data["dropoff_location"],
        current_cycle_used=data["current_cycle_used"],
        result=result,
    )

    return Response({"id": trip.id, **result}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def recent_trips(request):
    trips = Trip.objects.all()[:10]
    return Response(TripSerializer(trips, many=True).data)
