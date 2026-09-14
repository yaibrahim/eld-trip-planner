from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from . import geocode as geo
from . import hos
from .geocode import GeocodeError, RoutingError
from .models import Trip
from .serializers import (
    ErrorResponseSerializer,
    LocationSuggestQuerySerializer,
    LocationSuggestionSerializer,
    ReverseGeocodeQuerySerializer,
    ReverseGeocodeResponseSerializer,
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
    except Exception:
        return Response(
            {"detail": "Something went wrong planning this trip. Please check the locations and try again."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

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


@extend_schema(
    parameters=[LocationSuggestQuerySerializer],
    responses={200: LocationSuggestionSerializer(many=True)},
    summary="Live location autocomplete",
    description="Returns up to 5 place-name matches for a partial query, for a location input's autocomplete dropdown.",
)
@api_view(["GET"])
def geocode_suggest(request):
    query = request.query_params.get("q", "").strip()
    if len(query) < 2:
        return Response([])
    try:
        results = geo.suggest(query)
    except Exception:
        return Response([])
    return Response(results)


@extend_schema(
    parameters=[ReverseGeocodeQuerySerializer],
    responses={200: ReverseGeocodeResponseSerializer, 400: ErrorResponseSerializer},
    summary="Reverse geocode a lat/lon",
    description="Resolves a lat/lon (e.g. from the browser's geolocation API) to a place name, for a 'use my current location' button.",
)
@api_view(["GET"])
def geocode_reverse(request):
    try:
        lat = float(request.query_params.get("lat"))
        lon = float(request.query_params.get("lon"))
    except (TypeError, ValueError):
        return Response({"detail": "lat and lon query params are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        display_name = geo.reverse(lat, lon)
    except GeocodeError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"display_name": display_name})
