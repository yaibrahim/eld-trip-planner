from rest_framework import serializers

from .models import Trip


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255, help_text="Free-text place name, e.g. 'Chicago, IL'")
    pickup_location = serializers.CharField(max_length=255, help_text="Free-text place name, e.g. 'Indianapolis, IN'")
    dropoff_location = serializers.CharField(max_length=255, help_text="Free-text place name, e.g. 'Dallas, TX'")
    current_cycle_used = serializers.FloatField(
        min_value=0, max_value=70, help_text="Hours already used in the driver's 70-hour/8-day cycle"
    )


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            "id",
            "current_location",
            "pickup_location",
            "dropoff_location",
            "current_cycle_used",
            "result",
            "created_at",
        ]


# --- Response-only serializers, used solely to document the shape of
# trips.hos.plan_trip()'s output for the OpenAPI schema. The views return
# that plain dict directly rather than instantiating these.


class WaypointSerializer(serializers.Serializer):
    label = serializers.CharField()
    display_name = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class WaypointsSerializer(serializers.Serializer):
    current = WaypointSerializer()
    pickup = WaypointSerializer()
    dropoff = WaypointSerializer()


class RouteSerializer(serializers.Serializer):
    geometry = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2),
        help_text="Polyline for the whole trip as [lat, lon] pairs",
    )


class StopSerializer(serializers.Serializer):
    label = serializers.CharField()
    status = serializers.ChoiceField(choices=["OFF_DUTY", "SLEEPER_BERTH", "DRIVING", "ON_DUTY"])
    status_label = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    duration_hours = serializers.FloatField()
    lat = serializers.FloatField(allow_null=True)
    lon = serializers.FloatField(allow_null=True)


class SummarySerializer(serializers.Serializer):
    total_distance_miles = serializers.FloatField()
    total_driving_hours = serializers.FloatField()
    total_on_duty_hours = serializers.FloatField()
    total_trip_duration_hours = serializers.FloatField()
    num_days = serializers.IntegerField()
    fuel_stops = serializers.IntegerField()
    rest_breaks = serializers.IntegerField()
    reset_stops = serializers.IntegerField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()


class LogSegmentSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["OFF_DUTY", "SLEEPER_BERTH", "DRIVING", "ON_DUTY"])
    status_label = serializers.CharField()
    start_hour = serializers.FloatField(help_text="Decimal hour (0-24) into the calendar day")
    end_hour = serializers.FloatField()
    label = serializers.CharField()
    start_time = serializers.CharField(help_text="HH:MM")
    end_time = serializers.CharField(help_text="HH:MM")


class RecapSerializer(serializers.Serializer):
    on_duty_hours_today = serializers.FloatField()
    cycle_hours_used_through_today = serializers.FloatField()
    hours_available_tomorrow = serializers.FloatField()


class RemarkSerializer(serializers.Serializer):
    time = serializers.CharField(help_text="HH:MM")
    label = serializers.CharField()


class DailyLogSerializer(serializers.Serializer):
    date = serializers.DateField()
    segments = LogSegmentSerializer(many=True)
    totals = serializers.DictField(child=serializers.FloatField(), help_text="Total hours per duty status label")
    recap = RecapSerializer()
    remarks = RemarkSerializer(many=True)


class TripPlanResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    summary = SummarySerializer()
    waypoints = WaypointsSerializer()
    route = RouteSerializer()
    stops = StopSerializer(many=True)
    daily_logs = DailyLogSerializer(many=True)


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class LocationSuggestQuerySerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2, max_length=255, help_text="Partial place name typed so far")


class LocationSuggestionSerializer(serializers.Serializer):
    display_name = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class ReverseGeocodeQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class ReverseGeocodeResponseSerializer(serializers.Serializer):
    display_name = serializers.CharField()
