import os
import json
import re
import time
from google import genai

# ---------------- CONFIG ---------------- #

MODEL_NAME = "models/gemma-3-12b-it"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

INPUT_FILE = "RESUME_UJJWALCHORARIA.txt"
OUTPUT_FILE = "resume_json.json"

# ---------------- GEMINI SETUP ---------------- #

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise EnvironmentError("❌ GEMINI_API_KEY not set in environment")

# New google-genai client
CLIENT = genai.Client(api_key=API_KEY)

# ---------------- SCHEMA ---------------- #

RESUME_SCHEMA = {
    
    "profile": {
        "user_id": "",
        "name": "",
        "year": "",
        "department": "",
        "institution": "",
        "availability": "low | medium | high"
    },

    "skills": {
        "programming_languages": [],
        "frameworks_libraries": [],
        "tools_platforms": [],
        "core_cs_concepts": [],
        "domain_skills": []
    },

    "experience_level": {
        "overall": "beginner | intermediate | advanced",
        "by_domain": {
        "web_dev": "beginner | intermediate | advanced",
        "ml_ai": "beginner | intermediate | advanced",
        "systems": "beginner | intermediate | advanced",
        "security": "beginner | intermediate | advanced"
        }
    },

    "projects": [
        {
        "title": "",
        "description": "",
        "technologies": [],
        "domain": "",
        "role": "",
        "team_size": 0,
        "completion_status": "completed | ongoing"
        }
    ],

    "interests": {
        "technical": [],
        "problem_domains": [],
        "learning_goals": []
    },

    "collaboration_preferences": {
        "roles_preferred": [],
        "project_types": ["hackathon", "research", "startup", "open_source"],
        "team_size_preference": ""
    },

    "open_source": {
        "experience": "none | beginner | active | maintainer",
        "technologies": [],
        "contributions": 0
    },

    "achievements": {
        "hackathons": [],
        "certifications": [],
        "awards": []
    },

    "reputation_signals": {
        "completed_projects": 0,
        "average_rating": 0.0,
        "peer_endorsements": 0
    },

    "embeddings": {
        "skill_embedding_id": "",
        "project_embedding_id": "",
        "interest_embedding_id": ""
    }

}

# ---------------- PROMPT BUILDER ---------------- #

def build_prompt(resume_text: str) -> str:
    return f"""
You are an expert resume parser.

TASK:
- Convert raw OCR resume text into structured JSON
- Follow the schema EXACTLY
- DO NOT infer, guess, assume, or hallucinate any data.
- If a field is not present in the resume, return an empty string ("") or an empty array ([]).
- Normalize extracted terms where possible (e.g., "C++" instead of "cplusplus").
- Infer project domains from descriptions
- Return ONLY valid JSON
- No markdown, no explanations, no extra text
- Extract ONLY information that is explicitly present in the text.
- DO NOT create synthetic skills, projects, experience levels, or interests.



RESUME TEXT:
----------------
{resume_text}
----------------

REQUIRED JSON SCHEMA:
{json.dumps(RESUME_SCHEMA, indent=2)}
"""

# ---------------- JSON CLEANER ---------------- #

def extract_json(text: str) -> dict:
    """
    Extracts the first valid JSON object from model output.
    Handles cases where LLM adds extra text or malformed JSON.
    """
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[parse_resume] Direct JSON parse failed: {e}")
        pass

    # Extract JSON between first { and last }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("❌ No JSON object found in LLM response")

    json_str = match.group()
    
    # Try parsing extracted JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"[parse_resume] Extracted JSON parse failed at char {e.pos}: {e.msg}")
        
        # Common fixes for LLM JSON issues
        # 1. Fix trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 2. Fix missing commas between items
        json_str = re.sub(r'(["\d\]}])\s*\n\s*"', r'\1,\n"', json_str)
        
        # 3. Fix unescaped quotes in strings (basic)
        json_str = re.sub(r'(?<!\\)"(?=\s*[^:,}\]])', r'\\"', json_str)
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e2:
            # Still failed, return minimal valid structure
            print(f"[parse_resume] JSON repair failed, returning minimal schema")
            return RESUME_SCHEMA.copy()

# ---------------- PARSER ---------------- #

def parse_resume(resume_text: str) -> dict:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[parse_resume] Attempt {attempt}/{MAX_RETRIES}")
            response = CLIENT.models.generate_content(
                model=MODEL_NAME,
                contents=build_prompt(resume_text),
                config={
                    "temperature": 0,
                    "top_p": 1,
                    "top_k": 1,
                    "max_output_tokens": 2048,
                },
            )

            response_text = getattr(response, "text", "")
            print(f"[parse_resume] Response length: {len(response_text)} chars")
            
            parsed_json = extract_json(response_text)
            print(f"[parse_resume] Successfully parsed JSON with {len(parsed_json)} keys")
            return parsed_json

        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"[parse_resume] Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print("❌ All retries exhausted, returning minimal schema")
                return RESUME_SCHEMA.copy()

# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        resume_text = f.read()

    result = parse_resume(resume_text)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("✅ Resume successfully parsed")
    print(f"📄 Output saved to {OUTPUT_FILE}")
