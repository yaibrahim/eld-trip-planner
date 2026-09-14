from django.urls import path

from . import views

urlpatterns = [
    path("trips/plan/", views.plan_trip, name="plan-trip"),
    path("trips/", views.recent_trips, name="recent-trips"),
    path("geocode/suggest/", views.geocode_suggest, name="geocode-suggest"),
    path("geocode/reverse/", views.geocode_reverse, name="geocode-reverse"),
]
