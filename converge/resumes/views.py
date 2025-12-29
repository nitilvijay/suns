from django.shortcuts import render
from django.contrib import messages
from rest_framework import viewsets
from .models import Resume
from .serializers import ResumeSerializer
from profiles.models import Profile


class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer

#Getting the resume upload form and handling the post request
def upload_resume(request):
    if request.method == "POST":
        reg = request.POST.get("registration_number")
        f = request.FILES.get("file") #Only the file path
        try:
            profile = Profile.objects.get(registration_number=reg)
        except Profile.DoesNotExist:
            messages.error(request, "Profile not found. Please register first.")
            return render(request, "upload_resume.html")

        if not f:
            messages.error(request, "Please select a PDF file.")
            return render(request, "upload_resume.html")

        Resume.objects.update_or_create(
            profile=profile,
            defaults={"file": f},
        )
        messages.success(request, "Resume uploaded!")
    return render(request, "upload_resume.html")

