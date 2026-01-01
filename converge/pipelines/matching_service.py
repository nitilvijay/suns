from typing import List, Dict

from external.match_users_to_projects import (
    compute_semantic_similarity,
    semantic_gate,
    score_skill_match,
    score_experience_alignment,
    score_year_compatibility,
    score_reputation,
    score_availability,
    compute_final_score,
)

from projects.models import Project
from resumes.models import Resume


def match_users_for_project(project_id: int, top_n: int = 5) -> List[Dict]:
    """
    Use external matching components with DB data to rank candidates.
    Returns a list of dicts with score breakdowns.
    """
    print(f"\n{'='*60}")
    print(f"[matching_service] Starting match for project_id={project_id}, top_n={top_n}")
    print(f"{'='*60}")
    
    project = Project.objects.filter(pk=project_id).first()
    if not project:
        print(f"[matching_service] ❌ Project {project_id} not found")
        return []
    
    if not project.embedding:
        print(f"[matching_service] ❌ Project {project_id} has no embedding")
        return []

    proj_emb = project.embedding
    proj_json = project.metadata or {}
    
    print(f"[matching_service] Project: {project.title}")
    print(f"[matching_service] Project embedding dim: {len(proj_emb)}")
    print(f"[matching_service] Project metadata keys: {list(proj_json.keys())}")
    print(f"[matching_service] Required skills: {proj_json.get('required_skills', [])}")
    print()

    results = []
    total_resumes = Resume.objects.select_related("profile").count()
    resumes_with_embeddings = 0
    passed_gate = 0

    # Consider all resumes that have embeddings
    for idx, resume in enumerate(Resume.objects.select_related("profile").all(), 1):
        reg_num = resume.profile.registration_number
        
        if not resume.embedding:
            print(f"[{idx}/{total_resumes}] {reg_num}: ❌ No embedding")
            continue
        
        resumes_with_embeddings += 1
        
        # Phase 1: semantic gate
        passes, sem_score = semantic_gate(proj_emb, resume.embedding)
        
        print(f"[{idx}/{total_resumes}] {reg_num}: semantic_score={sem_score:.4f}, passes_gate={passes}")
        
        if not passes:
            continue
        
        passed_gate += 1

        # Phase 2: composite scoring
        user_json = resume.parsed_json or {}
        profile = user_json.get("profile", {})
        skills = user_json.get("skills", {})
        experience = user_json.get("experience_level", {})
        reputation = user_json.get("reputation_signals", {})

        required_skills = proj_json.get("required_skills", [])
        project_type = proj_json.get("project_type", "hackathon")

        skill_score = score_skill_match(required_skills, skills)
        experience_score = score_experience_alignment(
            project_type,
            experience.get("overall", "beginner"),
            experience.get("by_domain", {})
        )
        year_score = score_year_compatibility(profile.get("year", ""))
        reputation_score = score_reputation(
            reputation.get("average_rating", 0),
            reputation.get("completed_projects", 0)
        )
        availability_score = score_availability(profile.get("availability", "medium"))

        final_score = compute_final_score(
            sem_score,
            skill_score,
            experience_score,
            year_score,
            reputation_score,
            availability_score,
        )
        
        print(f"    └─ Final: {final_score:.4f} (skill={skill_score:.2f}, exp={experience_score:.2f}, year={year_score:.2f}, rep={reputation_score:.2f}, avail={availability_score:.2f})")

        results.append({
            "user_id": resume.profile.registration_number,
            "name": resume.profile.name or resume.profile.registration_number,
            "final_score": round(final_score, 4),
            "semantic_score": round(sem_score, 4),
            "skill_score": round(skill_score, 4),
            "experience_score": round(experience_score, 4),
            "year_score": round(year_score, 4),
            "reputation_score": round(reputation_score, 4),
            "availability_score": round(availability_score, 4),
        })

    # Sort and return top-n
    results.sort(key=lambda r: r["final_score"], reverse=True)
    
    print(f"\n{'='*60}")
    print(f"[matching_service] Summary:")
    print(f"  Total resumes: {total_resumes}")
    print(f"  With embeddings: {resumes_with_embeddings}")
    print(f"  Passed semantic gate: {passed_gate}")
    print(f"  Final matches: {len(results[:top_n])}")
    print(f"{'='*60}\n")
    
    return results[:top_n]