# Converge: Embeddings & Candidate Matching Microservice

## Overview

**Converge** is a Django-based microservice that generates semantic embeddings for resumes and projects, then matches candidates to projects using a two-layer scoring algorithm combining semantic relevance and peer ratings.

### Key Features
-  **Google GenAI Integration**: Uses `text-embedding-004` model for 768-dimensional semantic embeddings
-  **Two-Layer Matching Algorithm**:
-  **Layer 1 (Capability)**: Semantic similarity (45%) + skills match (35%) + experience alignment (20%)
-  **Layer 2 (Trust)**: Peer ratings (55%) + reliability signals (45%)
-  **Peer Rating System**: Community-driven trust scores with Bayesian smoothing
-  **Local Data Storage**: Stores canonical resume/project JSON locally—no shared database dependency
-  **CORS Enabled**: Ready for cross-origin requests from Spring Boot or frontend
-  **Production Ready**: Gunicorn + Nginx + PostgreSQL setup included

---

## Problem Brief & Solution

### The Problem

Many college project ideas fail not because they lack potential, but because students struggle to find like-minded collaborators beyond their immediate circles to bring their ideas to life. Additionally:

1. **Theory-Heavy Learning**: Students are unable to practically apply learned concepts and have reduced exposure to implementation friction because of passive, theory-heavy learning environments.

2. **Open-Source Barrier**: Beginners face a steep barrier when entering the open-source community, often discouraged by overwhelming codebases and the lack of small, beginner-friendly projects.

3. **Research Gap**: Many students lack exposure to the research ecosystem and face difficulty finding opportunities, despite the presence of faculty willing to mentor and guide them.

4. **Talent Invisibility**: No systematic way to discover and connect with complementary talent on campus.

### The Solution: Converge

Converge is a **campus-first collaboration platform** that enables students to discover, team up, and work on real-world projects and research, making them industry-ready professionals:

#### Core Features
- **Resume Intelligence**: Students upload their resumes/CVs and required data is extracted in a suitable format.
- **AI-Powered Matching**: Professors/Students post project ideas, and an AI-powered peer recommender system gives the top-N most suitable students using semantic embeddings and a custom-built matching algorithm.
- **Talent Visibility**: Improved talent visibility within the campus and a stronger peer-to-peer mentorship-cum-collaboration culture.
- **Research Exposure**: Dedicated space where faculty publish active research areas, expanding student exposure and research participation.
- **Project-Driven Learning**: Shift from passive theory to active, project-driven learning, emphasizing exposure to implementation friction.
- **Open-Source Onboarding**: Dedicated open-source section to provide open-source newcomers a first-hand experience in contributing.

---

## Technical Problem It Solves (Architecture Level)

1. **Cold Start Problem**: New candidates/projects have no historical data → Solved by semantic embeddings + default trust priors
2. **Matching at Scale**: Manual matching is slow → Automated two-layer algorithm scores all candidates in seconds
3. **Trust Without History**: Can't trust new community members → Peer rating system with Bayesian smoothing provides fair initial scores
4. **Coupled Architecture**: Sharing a database with Spring Boot backend creates tight coupling → Converge stores its own JSON copies, decoupling the services
5. **Embedding Quality**: Local/deterministic embeddings lose semantic nuance → Google GenAI embeddings capture real semantic meaning
6. **Inconsistent Scoring**: Different match requests give different results → Deterministic two-layer algorithm ensures consistency

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│          Spring Boot Backend (User/Project Mgmt)        │
└────────────────┬────────────────────────────────────────┘
                 │ POST resume/project JSON
                 ▼
┌─────────────────────────────────────────────────────────┐
│         Converge Microservice (Django)                  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Resumes    │  │   Projects   │  │   Ratings    │   │
│  │   Service    │  │   Service    │  │   Service    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                 │                  │            │
│         └─────────┬───────┴──────────────────┘            │
│                   ▼                                       │
│          ┌─────────────────────┐                         │
│          │  Google GenAI API   │ (Embeddings)            │
│          └─────────────────────┘                         │
│                   │                                       │
│         ┌─────────┴──────────────┐                       │
│         ▼                        ▼                        │
│    ┌─────────────┐        ┌──────────────┐              │
│    │Embedding DB │        │PostgreSQL DB │              │
│    │(768 floats) │        │(JSON + Meta) │              │
│    └─────────────┘        └──────────────┘              │
│                                                          │
└──────────────────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   POST /match/3      GET /health
        │                 │
        ▼                 ▼
  [Candidates]      [Server Status]
```

---

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Docker (optional, for containerized deployment)
- Google GenAI API Key

### Local Development

```bash
# 1. Clone and navigate
cd /home/nitil/brainfuel/suns/converge

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure .env
cat > .env << EOF
DB_NAME=converge_dev
DB_USER=converge_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your_django_secret_key
GEMINI_API_KEY=your_google_api_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
SECURE_SSL_REDIRECT=False
EOF

# 5. Run migrations
python manage.py migrate

# 6. Create superuser (optional, for admin panel)
python manage.py createsuperuser

# 7. Start development server
python manage.py runserver
```

### Docker Deployment

```bash
# From /home/nitil/brainfuel/suns/
docker-compose up --build

# Access at http://localhost:8000
```

### Server Deployment (Direct)

Follow [DEPLOYMENT.md](converge/DEPLOYMENT.md) for systemd + Nginx setup.

---

## API Endpoints

### 1. Store Resume + Generate Embedding
```bash
POST /api/resume/json/
{
  "resume_id": 123,
  "parsed_json": {
    "profile": { "name": "John Doe", "year": "2024" },
    "skills": { "Python": 5, "Django": 4 },
    "experience_level": { "overall": "intermediate" },
    "reputation_signals": { "average_rating": 4.2, "completed_projects": 5 }
  }
}
```

### 2. Store Project + Generate Embedding
```bash
POST /api/project/embed/
{
  "project_id": 456,
  "parsed_json": {
    "title": "AI Matching System",
    "description": "Build candidate-project matcher",
    "project_type": "project",
    "required_skills": ["Python", "Django"],
    "domains": ["backend", "ml"]
  }
}
```

### 3. Match Candidates to Project
```bash
POST /api/project/match/456/?top=5
Response: {
  "project_id": 456,
  "matches": [
    {
      "resume_id": 123,
      "final_score": 0.817,
      "layer1_capability": { "capability_score": 0.8934, ... },
      "layer2_trust": { "trust_score": 0.675, ... },
      "ratings": { "global_rating": 3.5, "ratings_count": 0 },
      "profile": { "name": "John Doe", "year": "2024" }
    }
  ],
  "count": 5
}
```

### 4. Submit Peer Rating
```bash
POST /api/ratings/submit/
{
  "rater_id": 10,
  "ratee_id": 123,
  "project_id": "456",
  "category_scores": {
    "technical": 4.5,
    "reliability": 4.0,
    "communication": 3.8,
    "initiative": 4.2,
    "overall": 4.1
  }
}
```

### 5. Get User's Global Rating
```bash
GET /api/ratings/user/123/
Response: {
  "global_rating": 4.1,
  "ratings_count": 3
}
```

### 6. Health Check
```bash
GET /health/
Response: {
  "status": "healthy",
  "database": "connected",
  "service": "Converge Embedding & Matching API"
}
```

---

## Scoring Algorithm

### Layer 1: Capability Score
```
capability_score = 0.45 × s_semantic + 0.35 × s_skills + 0.20 × s_experience
```
- `s_semantic`: Cosine similarity between embeddings (0-1)
- `s_skills`: Match ratio of required skills (0-1)
- `s_experience`: Experience level alignment (0-1)

### Layer 2: Trust Score
```
trust_score = 0.55 × s_rating + 0.45 × s_reliability
```
- `s_rating`: Bayesian-smoothed global rating (scaled 0-1)
- `s_reliability`: Completion ratio + availability (0-1)

### Final Score
```
final_score = α × capability_score + (1-α) × trust_score
```
- `α` varies by project type (default 0.65 for projects)

---

## Technical Deep Dive: Matching Algorithm

### 1. Embedding Generation

#### Tools & Libraries
- **google-genai** (v1.0+): Google's latest GenAI SDK
- **Model**: `text-embedding-004` (768-dimensional vectors)
- **Embedding Type**: RETRIEVAL_DOCUMENT (optimized for semantic search)

#### Process
```python
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)

# Build semantic text from resume/project JSON
semantic_text = f"""
TITLE: {title}
DESCRIPTION: {description}
SKILLS: {', '.join(skills)}
DOMAINS: {', '.join(domains)}
"""

# Generate embedding via Google GenAI
config = genai.types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
result = client.models.embed_content(
    model="models/text-embedding-004",
    content=semantic_text,
    config=config
)

embedding = result.embeddings[0].values  # 768 floats
```

**Key Advantages**:
- Semantic understanding (vs. TF-IDF or lexical matching)
- Handles synonyms and context
- Generalizes across similar terms
- Pre-trained on massive corpus

### 2. Semantic Relevance Filter (Phase 1)

#### Algorithm: Cosine Similarity Gating
```python
import numpy as np

def semantic_relevance_filter(proj_embedding, resume_embedding):
    """
    Compute cosine similarity and apply soft threshold.
    
    Returns: (passes_gate, similarity_score, interpretation)
    """
    # Normalize embeddings to unit vectors
    proj_norm = np.linalg.norm(proj_embedding)
    resume_norm = np.linalg.norm(resume_embedding)
    
    proj_unit = proj_embedding / proj_norm
    resume_unit = resume_embedding / resume_norm
    
    # Cosine similarity = dot product of unit vectors
    similarity = np.dot(proj_unit, resume_unit)
    
    # Soft threshold with interpretation
    if similarity >= 0.75:
        interpretation = "strong"
        passes = True
    elif similarity >= 0.65:
        interpretation = "moderate"
        passes = True
    elif similarity >= 0.55:
        interpretation = "weak"
        passes = False  # Soft gate
    else:
        interpretation = "poor"
        passes = False
    
    return passes, similarity, interpretation
```

**Thresholds**:
- `≥ 0.75`: Strong semantic match (likely related)
- `0.65-0.75`: Moderate match (probably related)
- `0.55-0.65`: Weak match (possibly related)
- `< 0.55`: Poor match (unrelated)

**Fallback Mechanism**: If no candidates pass the semantic gate (strict filtering), the system automatically falls back to the top-N by similarity score to ensure at least some matches are returned.

### 3. Skills Matching (Part of Capability)

#### Algorithm: Overlap Ratio
```python
def compute_skills_match(required_skills, candidate_skills):
    """
    Calculate skills match as ratio of matched required skills.
    
    Args:
        required_skills: List[str] from project
        candidate_skills: Dict[str, int] from resume (skill -> proficiency 1-5)
    
    Returns:
        float: 0-1, percentage of required skills candidate has
    """
    if not required_skills:
        return 1.0
    
    matched = sum(1 for skill in required_skills 
                  if skill.lower() in [s.lower() for s in candidate_skills.keys()])
    
    ratio = matched / len(required_skills)
    return min(ratio, 1.0)
```

**Scoring Rationale**:
- 100% match = candidate has all required skills
- 50% match = candidate has half the skills (may need to learn)
- 0% match = candidate lacks all required skills

### 4. Experience Alignment (Part of Capability)

#### Levels: Beginner → Intermediate → Advanced → Expert
```python
EXPERIENCE_HIERARCHY = {
    "beginner": 0.4,
    "intermediate": 0.7,
    "advanced": 0.9,
    "expert": 1.0
}

PROJECT_EXPERIENCE_REQUIREMENTS = {
    "hackathon": "intermediate",  # Can be done by intermediate devs
    "project": "advanced",         # Needs advanced skills
    "research": "expert"           # Research-level work
}

def compute_experience_alignment(project_type, candidate_level):
    """
    Calculate if candidate's experience matches project needs.
    
    Returns: float 0-1
    """
    required_level = PROJECT_EXPERIENCE_REQUIREMENTS.get(project_type, "intermediate")
    required_score = EXPERIENCE_HIERARCHY[required_level]
    candidate_score = EXPERIENCE_HIERARCHY.get(candidate_level.lower(), 0.4)
    
    # If candidate exceeds requirement, they're over-qualified (still good, return 1.0)
    if candidate_score >= required_score:
        return 1.0
    
    # If candidate is under-qualified, calculate ratio
    return candidate_score / required_score
```

### 5. Trust Scoring with Ratings

#### Bayesian Smoothing
```python
PRIOR_MEAN = 3.5        # Default trust level
PRIOR_WEIGHT = 3        # Strength of prior (high = trust new users more)

def get_global_rating_with_smoothing(ratee_id):
    """
    Compute Bayesian-smoothed global rating.
    
    Formula:
    smoothed = (prior_mean × prior_weight + sum_of_ratings) 
               / (prior_weight + rating_count)
    """
    ratings = Rating.objects.filter(ratee_id=ratee_id).all()
    count = ratings.count()
    
    if count == 0:
        # No ratings: return prior (new users start at 3.5/5)
        return PRIOR_MEAN
    
    sum_ratings = sum(r.adjusted_rating for r in ratings)
    smoothed = (PRIOR_MEAN * PRIOR_WEIGHT + sum_ratings) / (PRIOR_WEIGHT + count)
    
    return smoothed
```

**Why Bayesian?**:
- New users (0 ratings) → start at 3.5/5 (neutral, not penalized)
- 1 rating of 5.0 → converges to ~4.1/5 (not extreme)
- 10 ratings averaging 4.5 → converges to 4.5/5 (trusts data)
- Prevents abuse: Can't tank someone with 1 bad rating

#### Rating Category Weighting
```python
CATEGORY_WEIGHTS = {
    "technical": 0.30,      # Most important: can they code?
    "reliability": 0.25,    # Second: do they finish?
    "communication": 0.20,  # Third: can they explain?
    "initiative": 0.15,     # Fourth: do they take action?
    "overall": 0.10         # Last: aggregate score
}

def calculate_raw_rating(category_scores):
    """
    Weighted average of 5 categories.
    """
    raw = sum(
        category_scores.get(cat, 0) * weight
        for cat, weight in CATEGORY_WEIGHTS.items()
    )
    return round(raw, 3)
```

### 6. Reliability Score

#### Calculation
```python
def compute_reliability_score(completion_ratio, availability):
    """
    Assess candidate's execution reliability.
    
    Args:
        completion_ratio: float, 0-1 (completed_projects / total_projects)
        availability: str, one of ["low", "medium", "high"]
    
    Returns:
        float: 0-1 reliability score
    """
    availability_bonus = {
        "low": 0.5,       # Busy = risky
        "medium": 0.75,   # Normal = reliable
        "high": 1.0       # Available = very reliable
    }
    
    # Combine completion history + current availability
    reliability = 0.7 * completion_ratio + 0.3 * availability_bonus[availability]
    return reliability
```

### 7. Full Matching Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Load project embedding & JSON                            │
│    - Retrieve 768-D vector from DB                          │
│    - Load project metadata (skills, type, domains)          │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PHASE 1: Semantic Gate (Filter bad matches)             │
│    For each resume:                                         │
│      - Compute cosine_sim(proj_emb, resume_emb)            │
│      - Apply threshold (0.55-0.75)                         │
│      - Keep only semantic_sim > threshold                  │
│    Result: ~50-80% of candidates pass                      │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PHASE 2A: Capability Scoring (Potential)                │
│    For each passing resume:                                 │
│      - s_semantic = cosine similarity (already computed)    │
│      - s_skills = overlap_ratio(req_skills, can_skills)   │
│      - s_experience = exp_alignment(type, can_level)       │
│      - capability = 0.45×s_sem + 0.35×s_skil + 0.20×s_exp│
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. PHASE 2B: Trust Scoring (Execution)                     │
│    For each candidate:                                      │
│      - Get global_rating (with Bayesian smoothing)         │
│      - s_rating = global_rating / 5.0 (normalize)         │
│      - s_reliability = 0.7×comp_ratio + 0.3×availability  │
│      - trust = 0.55×s_rating + 0.45×s_reliability         │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Final Score Calculation                                  │
│    For each candidate:                                      │
│      - final_score = α × capability + (1-α) × trust       │
│      - α = PROJECT_TYPE_ALPHA[project_type]               │
│      - α = 0.65 for projects, 0.55 for hackathons         │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Sort & Return                                            │
│    - Sort by final_score descending                        │
│    - Return all matches with detailed breakdown            │
│    - Each match includes all 3 scores (sem, cap, trust)   │
└─────────────────────────────────────────────────────────────┘
```

### 8. Edge Cases & Fallbacks

| Scenario | Handling |
|----------|----------|
| No embeddings exist | 404 error (prompt user to POST embed first) |
| All candidates filtered by gate | Fallback to top-N by semantic score |
| No ratings for candidate | Use Bayesian prior (3.5/5) |
| Skills list empty in resume | Assume 0% match (0.0 score) |
| Experience level not specified | Default to "beginner" (0.4) |
| Availability not set | Default to "medium" (0.75) |
| Project type unknown | Use default α=0.65 |

### 9. Performance Characteristics

| Operation | Complexity | Time (1000 resumes) |
|-----------|-----------|-------------------|
| Semantic gate (cosine sim) | O(n × d) where d=768 | ~50ms |
| Skills matching | O(n × m) where m=avg skills | ~5ms |
| Experience alignment | O(n) | <1ms |
| Capability scoring | O(n) | ~3ms |
| Trust scoring | O(n × r) where r=avg ratings | ~10ms |
| Final scoring | O(n log n) sort | ~15ms |
| **Total** | - | **~85ms** |

---

## Technical Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `django` | 5.2.7 | Web framework |
| `djangorestframework` | 3.16.1 | REST API serializers |
| `psycopg2-binary` | 2.9.11 | PostgreSQL adapter |
| `google-genai` | ≥1.0.0 | Embedding generation |
| `numpy` | 2.1.2 | Vector operations |
| `scikit-learn` | 1.5.2 | ML utilities (unused currently, available for future) |
| `gunicorn` | 21.2.0 | WSGI app server |
| `whitenoise` | 6.6.0 | Static file serving |
| `django-cors-headers` | 4.3.1 | CORS middleware |
| `python-decouple` | 3.8 | Environment config |

---

## Bayesian Rating Smoothing

New users get a prior mean of **3.5** with weight of **3**:
```
global_rating = (prior_mean × prior_weight + sum_of_ratings) / (prior_weight + count)
```

This prevents new users from having artificially low/high scores and converges toward true average as more ratings accumulate.

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_NAME` | PostgreSQL database name | `converge_dev` |
| `DB_USER` | PostgreSQL user | `converge_user` |
| `DB_PASSWORD` | PostgreSQL password | `secure_pass` |
| `DB_HOST` | Database host | `localhost` or `database` (Docker) |
| `DB_PORT` | Database port | `5432` |
| `SECRET_KEY` | Django secret key (KEEP SECRET!) | `django-insecure-...` |
| `GEMINI_API_KEY` | Google GenAI API key | `AIzaSy...` |
| `DEBUG` | Debug mode | `False` (production) or `True` (dev) |
| `ALLOWED_HOSTS` | Allowed hostnames | `localhost,127.0.0.1,yourdomain.com` |
| `SECURE_SSL_REDIRECT` | Force HTTPS | `True` (production) |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `https://frontend.com` |

---

## Database Schema

### resumes_resumeembedding
- `resume_id` (int, pk)
- `semantic_text` (text)
- `embedding` (float array, 768 dims)
- `created_at`, `updated_at`

### resumes_resumejson
- `resume_id` (int, pk)
- `resume_json` (JSONB)
- `created_at`, `updated_at`

### projects_projectembedding
- `project_id` (int, pk)
- `semantic_text` (text)
- `embedding` (float array, 768 dims)
- `created_at`, `updated_at`

### projects_projectjson
- `project_id` (int, pk)
- `project_json` (JSONB)
- `created_at`, `updated_at`

### ratings_rating
- `id` (int, pk)
- `rater_id` (int)
- `ratee_id` (int)
- `project_id` (str)
- `category_scores` (JSONB)
- `raw_rating` (float)
- `adjusted_rating` (float)
- `created_at`

---

## Deployment

### Docker
```bash
docker-compose up --build
```

### Direct Server (Ubuntu/Debian)
```bash
# See DEPLOYMENT.md for full instructions
sudo systemctl start converge
sudo systemctl status converge
```

### Render/Cloud
Set environment variables and deploy via Git integration.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 400 on `/api/project/match/{id}` | Ensure project embedding exists (POST `/api/project/embed/` first) |
| PostgreSQL connection refused | Check DB_HOST, DB_PORT, credentials in .env |
| `GEMINI_API_KEY not configured` | Add `GEMINI_API_KEY` to .env or environment |
| CORS errors | Update `CORS_ALLOWED_ORIGINS` for frontend origin |
| 502 Bad Gateway (Nginx) | Check if Gunicorn is running: `sudo systemctl status converge` |

---

## Questions?

- **How does semantic matching work?** → We compute cosine similarity between 768-D embeddings from Google GenAI
- **Can I use a different embedding model?** → Yes, update `external/embed_resume.py` and `external/embed_project.py`
- **How do I deploy without Docker?** → Follow [DEPLOYMENT.md](converge/DEPLOYMENT.md)
- **Can ratings affect match scores in real-time?** → Yes, trust layer is recalculated per request
- **What if PostgreSQL goes down?** → Migrations will fail; restore the database and run `python manage.py migrate`

---

## Contributing

1. Create a feature branch
2. Make changes
3. Test with local server or Docker
4. Submit PR with description

---

## License

[Add your license here]

---

**Last Updated**: Jan 21, 2026  
**Maintainer**: Nitil Vijay  
