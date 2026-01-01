from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "profiles"
#URL generator for ViewSets class in views.py
router = DefaultRouter()
router.register(r"", views.ProfileViewSet, basename="profile")

urlpatterns = [
    #This router will automatically generate URLs for all the actions in ProfileViewSet, like list, create, retrieve, update, and destroy.  
    path("", include(router.urls)),
    path("register/", views.register, name="register"),
]