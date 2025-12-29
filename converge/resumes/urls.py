from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "resumes"
router = DefaultRouter()
router.register(r"", views.ResumeViewSet, basename="resume")

urlpatterns = [
    path("", include(router.urls)),
    path("upload/", views.upload_resume, name="upload"),
]
