"""
URL configuration for converge project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from profiles import views as profile_views
from resumes import views as resume_views
from converge import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/profiles/", include("profiles.urls")),
    path("api/resumes/", include("resumes.urls")),
    path("api/projects/", include("projects.urls")),
    # Simple HTML pages
    path("", core_views.home, name="home"),
    path("profiles/register/", profile_views.register, name="profiles-register"),
    path("resumes/upload/", resume_views.upload_resume, name="resumes-upload"),
    path("discover/", include("discovery.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
