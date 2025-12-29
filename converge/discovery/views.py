from django.shortcuts import render
from profiles.models import Profile
from projects.models import Project


def discover(request):
    # Get filters from query params
    project_type = request.GET.get("type", "all")
    department = request.GET.get("department", "")
    year = request.GET.get("year", "")
    
    # Campus Closed Projects - from Project table
    campus_closed = Project.objects.filter(project_type="campus_closed").select_related("owner_profile")
    if department:
        campus_closed = campus_closed.filter(owner_profile__department__icontains=department)
    if year:
        campus_closed = campus_closed.filter(owner_profile__year=year)
    
    # Campus & External OSS - from Profile table
    profiles = Profile.objects.all()
    
    if department:
        profiles = profiles.filter(department__icontains=department)
    if year:
        profiles = profiles.filter(year=year)
    
    # Parse campus OSS repos (one per line)
    campus_oss = []
    for profile in profiles:
        if profile.campus_oss_repos:
            repos = [url.strip() for url in profile.campus_oss_repos.split("\n") if url.strip()]
            for repo_url in repos:
                campus_oss.append({
                    "url": repo_url,
                    "owner": profile.name or profile.registration_number,
                    "department": profile.department,
                    "year": profile.year,
                })
    
    # Parse external OSS contributions (one per line)
    external_oss = []
    for profile in profiles:
        if profile.external_oss_contributions:
            repos = [url.strip() for url in profile.external_oss_contributions.split("\n") if url.strip()]
            for repo_url in repos:
                external_oss.append({
                    "url": repo_url,
                    "contributor": profile.name or profile.registration_number,
                    "department": profile.department,
                    "year": profile.year,
                })
    
    # Get unique departments and years for filter dropdowns
    departments = Profile.objects.values_list("department", flat=True).distinct().order_by("department")
    years = Profile.objects.values_list("year", flat=True).distinct().order_by("year")
    
    context = {
        "campus_closed": campus_closed,
        "campus_oss": campus_oss,
        "external_oss": external_oss,
        "project_type": project_type,
        "selected_department": department,
        "selected_year": year,
        "departments": [d for d in departments if d],
        "years": [y for y in years if y],
    }
    
    return render(request, "discover.html", context)

