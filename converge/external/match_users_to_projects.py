import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple

# -------- CONFIG --------
SEMANTIC_THRESHOLD = -0.5  # Very permissive for deterministic embeddings

# Weights (must sum to 1.0) - reduced semantic weight, increased skill/experience
WEIGHTS = {
    "semantic": 0.20,
    "skill": 0.30,
    "experience": 0.20,
    "year": 0.12,
    "reputation": 0.10,
    "availability": 0.08
}

# Experience level mapping
EXPERIENCE_LEVELS = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3
}

# Project type to preferred experience mapping
PROJECT_TYPE_EXPERIENCE = {
    "hackathon": "intermediate",
    "research": "advanced",
    "startup": "intermediate",
    "open_source": "beginner"
}

# -------- HELPER FUNCTIONS --------
def load_project_embeddings() -> Dict:
    """Load project embeddings from file."""
    try:
        with open("project_embeddings.json", "r") as f:
            data = json.load(f)
            # Convert to dict keyed by project_id
            return {proj["project_id"]: proj for proj in data}
    except FileNotFoundError:
        print("❌ project_embeddings.json not found")
        return {}

def load_user_embeddings() -> Dict:
    """Load user embeddings from file."""
    try:
        with open("user_embeddings.json", "r") as f:
            data = json.load(f)
            # Convert to dict keyed by user_id
            return {user["user_id"]: user for user in data}
    except FileNotFoundError:
        print("❌ user_embeddings.json not found")
        return {}

def load_project_json(project_id: str) -> Dict:
    """Load individual project JSON file."""
    try:
        with open(f"project_jsons/{project_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_user_json(resume_file: str) -> Dict:
    """Load individual user JSON file."""
    try:
        with open(f"resume_jsons/{resume_file}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# -------- PHASE 1: SEMANTIC GATE --------
def compute_semantic_similarity(project_embedding: list, user_embedding: list) -> float:
    """
    Compute cosine similarity between project and user embeddings.
    
    Args:
        project_embedding: Project embedding vector
        user_embedding: User embedding vector
    
    Returns:
        float: Cosine similarity score (0-1)
    """
    proj_vec = np.array(project_embedding).reshape(1, -1)
    user_vec = np.array(user_embedding).reshape(1, -1)
    
    similarity = cosine_similarity(proj_vec, user_vec)[0][0]
    return float(similarity)

def semantic_gate(
    project_embedding: list,
    user_embedding: list,
    threshold: float = SEMANTIC_THRESHOLD
) -> Tuple[bool, float]:
    """
    PHASE 1: Semantic Gate
    
    Compute cosine similarity and check if it exceeds threshold.
    
    Args:
        project_embedding: Project embedding vector
        user_embedding: User embedding vector
        threshold: Semantic similarity threshold (default: 0.35)
    
    Returns:
        Tuple[passes_gate, similarity_score]
    """
    similarity = compute_semantic_similarity(project_embedding, user_embedding)
    passes = similarity >= threshold
    
    return passes, similarity

# -------- PHASE 2: COMPOSITE SCORING --------

def score_skill_match(
    required_skills: List[str],
    user_skills: Dict[str, list]
) -> float:
    """
    SIGNAL 2: Skill Match Score
    
    Measures overlap between required skills and user skills.
    
    Formula:
        Skill_Match_Score = |Required_Skills ∩ User_Skills| / |Required_Skills|
    
    Args:
        required_skills: List of required skills from project
        user_skills: Dict containing user's skills by category
    
    Returns:
        float: Skill match score (0-1)
    """
    if not required_skills:
        return 1.0  # No requirements = perfect score
    
    # Flatten all user skills
    all_user_skills = set()
    for skill_list in user_skills.values():
        if isinstance(skill_list, list):
            all_user_skills.update([s.lower() for s in skill_list])
    
    # Normalize required skills
    required_normalized = set([s.lower() for s in required_skills])
    
    # Compute intersection
    intersection = len(required_normalized & all_user_skills)
    
    # Compute score
    score = intersection / len(required_normalized)
    
    return min(1.0, score)

def score_experience_alignment(
    project_type: str,
    user_overall_experience: str,
    user_domain_experience: Dict[str, str]
) -> float:
    """
    SIGNAL 3: Experience Alignment Score
    
    Measures whether user's experience matches project type.
    
    Args:
        project_type: Type of project (hackathon, research, startup, open_source)
        user_overall_experience: User's overall experience level
        user_domain_experience: User's experience by domain
    
    Returns:
        float: Experience alignment score (0-1)
    """
    preferred_level = PROJECT_TYPE_EXPERIENCE.get(project_type, "intermediate")
    preferred_value = EXPERIENCE_LEVELS.get(preferred_level, 2)
    user_value = EXPERIENCE_LEVELS.get(user_overall_experience, 1)
    
    # Scoring: exact match = 1.0, below = 0.3, above = 0.8
    if user_value == preferred_value:
        return 1.0
    elif user_value < preferred_value:
        return 0.3
    else:  # user_value > preferred_value
        return 0.8

def score_year_compatibility(
    user_year: str,
    preferred_year: int = None
) -> float:
    """
    SIGNAL 4: Year Compatibility Score
    
    Softly penalizes year mismatches without hard blocking.
    
    Formula:
        year_diff = abs(user_year - preferred_year)
        Year_Score = max(0, 1 - 0.25 * year_diff)
    
    Args:
        user_year: User's year in program (e.g., "2024", "2025")
        preferred_year: Preferred year (optional)
    
    Returns:
        float: Year compatibility score (0-1)
    """
    if preferred_year is None:
        return 1.0  # Unknown preference = no penalty
    
    try:
        user_year_int = int(user_year)
        year_diff = abs(user_year_int - preferred_year)
        score = max(0.0, 1.0 - (0.25 * year_diff))
        return min(1.0, score)
    except (ValueError, TypeError):
        return 1.0  # Invalid year data = no penalty

def score_reputation(
    average_rating: float,
    completed_projects: int
) -> float:
    """
    SIGNAL 5: Reputation / Rating Score
    
    Measures user credibility without punishing new users.
    
    Formula:
        confidence_factor = min(1, completed_projects / 5)
        Reputation_Score = (average_rating / 5) * confidence_factor
    
    Rules:
        - New users (0 ratings) NOT punished
        - Missing data degrades gracefully
    
    Args:
        average_rating: Average user rating (0-5)
        completed_projects: Number of completed projects
    
    Returns:
        float: Reputation score (0-1)
    """
    if completed_projects == 0:
        return 1.0  # New users = perfect score (no penalty)
    
    # Confidence factor: scales from 0 to 1 as completed_projects increases
    confidence_factor = min(1.0, completed_projects / 5.0)
    
    # Normalize rating to 0-1 scale
    normalized_rating = average_rating / 5.0 if average_rating > 0 else 1.0
    
    # Final score
    score = normalized_rating * confidence_factor
    
    return min(1.0, score)

def score_availability(availability: str) -> float:
    """
    SIGNAL 6: Availability Score
    
    Simple mapping from availability level to score.
    
    Args:
        availability: Availability level (high, medium, low)
    
    Returns:
        float: Availability score (0-1)
    """
    availability_map = {
        "high": 1.0,
        "medium": 0.7,
        "low": 0.4
    }
    
    return availability_map.get(availability.lower(), 0.5)

def compute_final_score(
    semantic_score: float,
    skill_score: float,
    experience_score: float,
    year_score: float,
    reputation_score: float,
    availability_score: float,
    weights: Dict[str, float] = WEIGHTS
) -> float:
    """
    PHASE 2: Compute Final Composite Score
    
    FINAL_SCORE =
        0.20 * semantic_similarity
      + 0.30 * skill_match
      + 0.20 * experience_alignment
      + 0.12 * year_compatibility
      + 0.10 * reputation
      + 0.08 * availability
    
    Args:
        semantic_score: Semantic similarity (0-1)
        skill_score: Skill match score (0-1)
        experience_score: Experience alignment score (0-1)
        year_score: Year compatibility score (0-1)
        reputation_score: Reputation score (0-1)
        availability_score: Availability score (0-1)
        weights: Weight dictionary
    
    Returns:
        float: Final composite score (0-1)
    """
    final_score = (
        weights["semantic"] * semantic_score +
        weights["skill"] * skill_score +
        weights["experience"] * experience_score +
        weights["year"] * year_score +
        weights["reputation"] * reputation_score +
        weights["availability"] * availability_score
    )
    
    return min(1.0, final_score)

# -------- MAIN MATCHING ENGINE --------
def match_users_to_project(project_id: str) -> List[Dict]:
    """
    Complete two-phase matching algorithm.
    
    PHASE 1: Semantic Gate
        - Filter users by semantic similarity threshold
    
    PHASE 2: Composite Scoring
        - Rank passing users by weighted composite score
    
    Args:
        project_id: Project ID to match users for
    
    Returns:
        List[Dict]: Ranked list of matching users with all scores
    """
    
    # Load data
    project_embeddings = load_project_embeddings()
    user_embeddings = load_user_embeddings()
    
    if project_id not in project_embeddings:
        print(f"❌ Project {project_id} not found in embeddings")
        return []
    
    project_data = project_embeddings[project_id]
    project_json = load_project_json(project_id)
    project_embedding = project_data["embedding"]
    
    matches = []
    
    print(f"\n{'='*70}")
    print(f"MATCHING USERS TO PROJECT: {project_id}")
    print(f"PROJECT TITLE: {project_data['title']}")
    print(f"{'='*70}\n")
    
    # -------- PHASE 1: SEMANTIC GATE --------
    print("PHASE 1: SEMANTIC GATE (Hard Filter)")
    print(f"Threshold: {SEMANTIC_THRESHOLD}\n")
    
    phase1_passes = []
    
    for user_id, user_data in user_embeddings.items():
        user_embedding = user_data["embedding"]
        resume_file = user_data.get("resume_file", user_id)
        
        # Compute semantic similarity
        passes_gate, semantic_score = semantic_gate(project_embedding, user_embedding)
        
        if passes_gate:
            phase1_passes.append({
                "user_id": user_id,
                "resume_file": resume_file,
                "semantic_score": semantic_score,
                "user_data": user_data,
                "user_json": load_user_json(resume_file)
            })
            print(f"  ✓ {user_id}: {semantic_score:.4f} (PASS)")
        else:
            print(f"  ✗ {user_id}: {semantic_score:.4f} (FAIL)")
    
    print(f"\nPhase 1 Result: {len(phase1_passes)} / {len(user_embeddings)} users passed\n")
    
    if not phase1_passes:
        print("⚠️  No users passed semantic gate")
        return []
    
    # -------- PHASE 2: COMPOSITE SCORING --------
    print("PHASE 2: COMPOSITE SUITABILITY SCORING")
    print(f"{'='*70}\n")
    
    for candidate in phase1_passes:
        user_id = candidate["user_id"]
        resume_file = candidate["resume_file"]
        semantic_score = candidate["semantic_score"]
        user_json = candidate["user_json"]
        
        # Extract user data from JSON
        profile = user_json.get("profile", {})
        skills = user_json.get("skills", {})
        experience = user_json.get("experience_level", {})
        reputation = user_json.get("reputation_signals", {})
        
        # Extract project requirements
        required_skills = project_json.get("required_skills", [])
        project_type = project_json.get("project_type", "hackathon")
        
        # Compute individual scores
        skill_score = score_skill_match(required_skills, skills)
        experience_score = score_experience_alignment(
            project_type,
            experience.get("overall", "beginner"),
            experience.get("by_domain", {})
        )
        year_score = score_year_compatibility(profile.get("year", "2024"))
        reputation_score = score_reputation(
            reputation.get("average_rating", 0),
            reputation.get("completed_projects", 0)
        )
        availability_score = score_availability(profile.get("availability", "medium"))
        
        # Compute final score
        final_score = compute_final_score(
            semantic_score,
            skill_score,
            experience_score,
            year_score,
            reputation_score,
            availability_score
        )
        
        match_record = {
            "user_id": user_id,
            "resume_file": resume_file,
            "final_score": round(final_score, 4),
            "semantic_score": round(semantic_score, 4),
            "skill_score": round(skill_score, 4),
            "experience_score": round(experience_score, 4),
            "year_score": round(year_score, 4),
            "reputation_score": round(reputation_score, 4),
            "availability_score": round(availability_score, 4),
            "profile": {
                "name": profile.get("name", "Unknown"),
                "year": profile.get("year", "Unknown"),
                "availability": profile.get("availability", "Unknown")
            },
            "score_breakdown": {
                "w_semantic": WEIGHTS["semantic"] * semantic_score,
                "w_skill": WEIGHTS["skill"] * skill_score,
                "w_experience": WEIGHTS["experience"] * experience_score,
                "w_year": WEIGHTS["year"] * year_score,
                "w_reputation": WEIGHTS["reputation"] * reputation_score,
                "w_availability": WEIGHTS["availability"] * availability_score
            }
        }
        
        matches.append(match_record)
    
    # Sort by final score (descending)
    matches.sort(key=lambda x: x["final_score"], reverse=True)
    
    return matches

# -------- OUTPUT & DISPLAY --------
def display_matches(matches: List[Dict], top_k: int = 5):
    """
    Display ranked matches in human-readable format.
    
    Args:
        matches: List of match records
        top_k: Number of top matches to display
    """
    if not matches:
        print("\n⚠️  No matches found")
        return
    
    print(f"\n{'='*70}")
    print(f"TOP {min(top_k, len(matches))} MATCHES")
    print(f"{'='*70}\n")
    
    for rank, match in enumerate(matches[:top_k], 1):
        print(f"RANK {rank}: {match['profile']['name']} ({match['user_id']})")
        print(f"  Final Score: {match['final_score']:.4f}")
        print(f"  ├─ Semantic:     {match['semantic_score']:.4f} (×0.20 = {match['score_breakdown']['w_semantic']:.4f})")
        print(f"  ├─ Skill Match:  {match['skill_score']:.4f} (×0.30 = {match['score_breakdown']['w_skill']:.4f})")
        print(f"  ├─ Experience:   {match['experience_score']:.4f} (×0.20 = {match['score_breakdown']['w_experience']:.4f})")
        print(f"  ├─ Year Compat:  {match['year_score']:.4f} (×0.12 = {match['score_breakdown']['w_year']:.4f})")
        print(f"  ├─ Reputation:   {match['reputation_score']:.4f} (×0.10 = {match['score_breakdown']['w_reputation']:.4f})")
        print(f"  └─ Availability: {match['availability_score']:.4f} (×0.08 = {match['score_breakdown']['w_availability']:.4f})")
        print(f"  Profile: {match['profile']['year']}, {match['profile']['availability']} availability")
        print()

def export_matches_json(matches: List[Dict], output_file: str = "matches.json"):
    """
    Export matches to JSON file.
    
    Args:
        matches: List of match records
        output_file: Output file path
    """
    with open(output_file, "w") as f:
        json.dump(matches, f, indent=2)
    print(f"✅ Matches exported to {output_file}")

# -------- MAIN --------
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("❌ Usage: python match_users_to_projects.py <project_id>")
        print("Example: python match_users_to_projects.py proj_694740e0")
        sys.exit(1)
    
    project_id = sys.argv[1]
    
    # Run matching algorithm
    matches = match_users_to_project(project_id)
    
    # Display results
    display_matches(matches, top_k=5)
    
    # Export to JSON
    if matches:
        export_matches_json(matches, f"matches_{project_id}.json")
