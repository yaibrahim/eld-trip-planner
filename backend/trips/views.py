from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from . import hos
from .geocode import GeocodeError, RoutingError
from .models import Trip
from .serializers import (
    ErrorResponseSerializer,
    TripPlanRequestSerializer,
    TripPlanResponseSerializer,
    TripSerializer,
)


@extend_schema(
    request=TripPlanRequestSerializer,
    responses={201: TripPlanResponseSerializer, 400: ErrorResponseSerializer},
    examples=[
        OpenApiExample(
            "Cross-country trip",
            value={
                "current_location": "Chicago, IL",
                "pickup_location": "Indianapolis, IN",
                "dropoff_location": "Dallas, TX",
                "current_cycle_used": 20,
            },
            request_only=True,
        ),
    ],
    summary="Plan a trip and generate ELD daily logs",
    description=(
        "Geocodes the three locations, fetches a driving route (current -> pickup -> "
        "dropoff), simulates the trip against FMCSA hours-of-service rules for a "
        "property-carrying driver on a 70-hour/8-day cycle, and returns the route, "
        "the stops/rests it inserted, and one Daily Log Sheet per calendar day."
    ),
)
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


@extend_schema(
    responses={200: TripSerializer(many=True)},
    summary="List recent trips",
    description="Returns the 10 most recently computed trips, each with its full cached result.",
)
@api_view(["GET"])
def recent_trips(request):
    trips = Trip.objects.all()[:10]
    return Response(TripSerializer(trips, many=True).data)
