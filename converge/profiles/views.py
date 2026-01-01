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
        # Extract form data
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
            # Create profile first
            profile = Profile.objects.create(**data)
            messages.success(request, f"Profile created for {data['name']}!")
            
            # Check if resume was uploaded
            resume_file = request.FILES.get("resume")
            if resume_file:
                # Import here to avoid circular dependency
                from resumes.models import Resume
                from pipelines.resume_pipeline import process_resume_instance
                
                # Create resume linked to profile
                resume = Resume.objects.create(
                    profile=profile,
                    file=resume_file
                )
                
                # Process resume (OCR → parse → embed → consolidate profile_json)
                result = process_resume_instance(resume)
                
                if result:
                    messages.success(
                        request,
                        f"Resume processed! ({result['text_len']} chars, {result['embedding_dim']} dims)"
                    )
                else:
                    messages.warning(request, "Resume uploaded but processing had errors. Check logs.")
            else:
                # No resume uploaded, just build basic profile_json from form
                profile.profile_json = {
                    "profile": {
                        "user_id": data["registration_number"],
                        "name": data["name"],
                        "registration_number": data["registration_number"],
                        "department": data["department"],
                        "course": data["course"],
                        "year": data["year"],
                        "availability": "medium"
                    },
                    "collaboration_preferences": {
                        "roles_preferred": [r.strip() for r in data["preferred_roles"].split(",") if r.strip()],
                        "project_types": ["hackathon", "research", "startup", "open_source"],
                    },
                    "experience_level": {
                        "overall": data["experience_level"] or "beginner"
                    }
                }
                profile.save(update_fields=["profile_json"])
                messages.info(request, "Profile created. Upload resume later to complete your profile.")
            
            # Redirect to the non-API HTML route
            return HttpResponseRedirect(reverse("profiles-register"))
            
        except Exception as e:
            messages.error(request, f"Error: {e}")
            import traceback
            print(traceback.format_exc())

    return render(request, "register.html")

