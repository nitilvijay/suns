from django.urls import path
from . import views

app_name = "discovery"

urlpatterns = [
    path("", views.discover, name="discover"),
]
