from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "projects"
router = DefaultRouter()
router.register(r"", views.ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
]
