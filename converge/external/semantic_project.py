def build_semantic_text_project(project_json: dict) -> str:
    """
    Converts project JSON into semantic text for embedding.
    
    Args:
        project_json: Structured project JSON
    
    Returns:
        str: Semantic text representation
    """
    
    sections = []
    
    # -------- PROJECT TITLE & DESCRIPTION --------
    if project_json.get("title"):
        sections.append(f"PROJECT TITLE:\n{project_json['title']}")
    
    if project_json.get("description"):
        sections.append(f"PROJECT DESCRIPTION:\n{project_json['description']}")
    
    # -------- PROJECT REQUIREMENTS --------
    required_skills = project_json.get("required_skills", [])
    if required_skills:
        sections.append(
            "PROJECT REQUIREMENTS:\n" + ", ".join(sorted(set(required_skills)))
        )
    
    # -------- PREFERRED TECHNOLOGIES --------
    preferred_tech = project_json.get("preferred_technologies", [])
    if preferred_tech:
        sections.append(
            "PREFERRED TECHNOLOGIES:\n" + ", ".join(sorted(set(preferred_tech)))
        )
    
    # -------- PROJECT DOMAINS --------
    domains = project_json.get("domains", [])
    if domains:
        sections.append(
            "PROJECT DOMAINS:\n" + ", ".join(sorted(set(domains)))
        )
    
    # -------- PROJECT TYPE --------
    if project_json.get("project_type"):
        sections.append(
            f"PROJECT TYPE:\n{project_json['project_type'].upper()}"
        )
    
    # -------- FINAL SEMANTIC TEXT --------
    return "\n\n".join(sections)

# -------- MAIN (FOR TESTING) --------
if __name__ == "__main__":
    import json
    

