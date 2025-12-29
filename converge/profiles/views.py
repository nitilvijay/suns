from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from rest_framework import viewsets
from .models import Profile
from .serializers import ProfileSerializer

'''This viewset automatically provides `list`, `create`, `retrieve`,
`update` and `destroy` actions for Profile model.
no need to use orm queries manually.
Makes use of DRF's ModelViewSet

HTTP Method	    Action
GET	                list profiles
GET /id/	        retrieve profile
POST	            create profile

We dont need to write separate methods for each action.
The funtion will take care of it automatically.
'''

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

def register(request):
    if request.method == "POST":
        data = {
            "name": request.POST.get("name", ""),
            "registration_number": request.POST.get("registration_number"),
            "department": request.POST.get("department", ""),
            "course": request.POST.get("course", ""),
            "year": request.POST.get("year") or None,
            "interest_type": request.POST.get("interest_type", "both"),
            "preferred_roles": request.POST.get("preferred_roles", ""),
            "experience_level": request.POST.get("experience_level", ""),
            "campus_oss_repos": request.POST.get("campus_oss_repos", ""),
            "external_oss_contributions": request.POST.get("external_oss_contributions", ""),
        }
        try:
            Profile.objects.create(**data)
            messages.success(request, "Registration successful!")
            # Redirect to the non-API HTML route
            return HttpResponseRedirect(reverse("profiles-register"))
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, "register.html")

