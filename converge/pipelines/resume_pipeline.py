from typing import Optional
import os
from decouple import config

# Note: import external modules lazily inside the function after setting GEMINI_API_KEY


def process_resume_instance(resume) -> Optional[dict]:
    """
    Run OCR → LLM parse → semantic reduce → embed on a Resume instance.
    Stores results back on the model.
    Returns a summary dict or None on failure.
    """
    try:
        # Ensure GEMINI_API_KEY available for external modules
        if not os.getenv("GEMINI_API_KEY"):
            gemini_key = config("GEMINI_API_KEY", default=None)
            if gemini_key:
                os.environ["GEMINI_API_KEY"] = gemini_key
        pdf_path = resume.file.path

        # Lazy imports after env var is ensured
        from external.ocr1 import extract_text_from_pdf
        from external.parse_resume import parse_resume
        from external.semantic import build_semantic_text
        from external.embed_resume import embed_semantic_text

        print("[resume_pipeline] OCR starting...")
        raw_text = extract_text_from_pdf(pdf_path)
        print(f"[resume_pipeline] OCR done (chars={len(raw_text) if raw_text else 0})")

        print("[resume_pipeline] Parse starting...")
        parsed_json = parse_resume(raw_text)
        print("[resume_pipeline] Parse done")

        print("[resume_pipeline] Semantic build starting...")
        semantic_text = build_semantic_text(parsed_json)
        print(f"[resume_pipeline] Semantic done (chars={len(semantic_text) if semantic_text else 0})")

        print("[resume_pipeline] Embedding starting...")
        embedding = embed_semantic_text(semantic_text)
        print(f"[resume_pipeline] Embedding done (dim={len(embedding) if embedding else 0})")

        # Persist resume data
        resume.raw_text = raw_text
        resume.parsed_json = parsed_json
        resume.semantic_text = semantic_text
        resume.embedding = embedding
        resume.save(update_fields=[
            "raw_text", "parsed_json", "semantic_text", "embedding"
        ])
        print("[resume_pipeline] Persisted resume with embedding length:", len(resume.embedding or []))

        # Consolidate profile_json with resume data
        if resume.profile:
            profile = resume.profile
            print("[resume_pipeline] Consolidating profile_json...")
            
            # Merge form data with resume parsed data
            profile_json = profile.profile_json or {}
            profile_section = profile_json.get("profile", {})
            
            # Extract key info from parsed resume
            resume_profile = parsed_json.get("profile", {})
            skills = parsed_json.get("skills", {})
            experience = parsed_json.get("experience_level", {})
            projects = parsed_json.get("projects", [])
            interests = parsed_json.get("interests", {})
            
            # Consolidate into complete profile_json
            profile.profile_json = {
                "profile": {
                    "user_id": profile.registration_number,
                    "name": profile.name or resume_profile.get("name", ""),
                    "registration_number": profile.registration_number,
                    "year": profile.year or resume_profile.get("year", ""),
                    "department": profile.department or resume_profile.get("department", ""),
                    "institution": resume_profile.get("institution", ""),
                    "availability": resume_profile.get("availability", "medium")
                },
                "skills": skills,
                "experience_level": experience,
                "projects": projects,
                "interests": interests,
                "collaboration_preferences": {
                    "roles_preferred": [r.strip() for r in (profile.preferred_roles or "").split(",") if r.strip()],
                    "project_types": ["hackathon", "research", "startup", "open_source"],
                    "team_size_preference": ""
                },
                "open_source": parsed_json.get("open_source", {}),
                "achievements": parsed_json.get("achievements", {}),
                "reputation_signals": parsed_json.get("reputation_signals", {})
            }
            profile.save(update_fields=["profile_json"])
            print(f"[resume_pipeline] Profile {profile.registration_number} consolidated")

        return {
            "text_len": len(raw_text or ""),
            "embedding_dim": len(embedding or []),
        }

    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"ERROR in resume pipeline: {str(e)}")
        print(traceback.format_exc())
        return None