import os
import requests
import html
import sys

# --- CONFIGURATION ---
LOGIN = "abataill"
MAX_SKILL_LEVEL = 21.0
CARD_WIDTH = 800

def get_token():
    """Authenticates with the 42 API to get an access token."""
    API_UID = os.getenv("API_UID")
    API_SECRET = os.getenv("API_SECRET")
    if not API_UID or not API_SECRET:
        raise Exception("ERROR: API_UID and API_SECRET not found in repository secrets.")
    
    response = requests.post(
        "https://api.intra.42.fr/oauth/token",
        data={"grant_type": "client_credentials", "client_id": API_UID, "client_secret": API_SECRET}
    )
    response.raise_for_status()
    return response.json()["access_token"]

def generate_svg_body(data):
    """Generates the content part of the SVG."""
    # --- Data Processing ---
    cursus_data = next((c for c in data["cursus_users"] if c["cursus_id"] == 21), None)
    if not cursus_data:
        raise Exception("ERROR: Cursus ID 21 not found for this user.")

    level_float = cursus_data.get("level", 0.0)
    rncp_percent = min((level_float / 21) * 100, 100)
    skills = sorted(cursus_data.get("skills", []), key=lambda x: x['level'], reverse=True)
    
    projects_data = data.get("projects_users", [])
    in_progress_projects = [
        p for p in projects_data 
        if p['status'] == 'in_progress' 
        and p['cursus_ids'] == [21] 
        and p['project']['name'] != 'Exam Rank 04'
    ]

    # --- LAYOUT & SIZING ---
    padding = 20
    section_gap = 20
    
    # Calculate content positions
    header_y = padding
    skills_y = header_y + 100 + section_gap
    num_skill_rows = (len(skills[:10]) + 1) // 2
    projects_y = skills_y + 30 + (num_skill_rows * 35) + section_gap if in_progress_projects else 0
    
    # --- SVG String Building ---
    body = ""

    # Header section
    body += f'<g transform="translate(30, {header_y})">'
    body += '<text y="0" style="font: 600 14px \'Segoe UI\', Arial, sans-serif; text-transform: uppercase;" fill="#c9d1d9">Current Level</text>'
    body += f'<text y="35" style="font: 700 28px \'Segoe UI\', Arial, sans-serif;" fill="#58a6ff">{level_float:.2f}</text>'
    body += f'<rect y="50" width="350" height="12" rx="6" fill="#21262d" />'
    body += f'<rect y="50" width="{350 * (level_float - int(level_float))}" height="12" rx="6" fill="#58a6ff" />'
    body += '</g>'
    body += f'<g transform="translate(420, {header_y})">'
    body += '<text y="0" style="font: 600 14px \'Segoe UI\', Arial, sans-serif; text-transform: uppercase;" fill="#c9d1d9">Progress to RNCP Level 7</text>'
    body += f'<text y="35" style="font: 700 28px \'Segoe UI\', Arial, sans-serif;" fill="#bc8cff">{rncp_percent:.0f}%</text>'
    body += f'<rect y="50" width="350" height="12" rx="6" fill="#21262d" />'
    body += f'<rect y="50" width="{350 * (rncp_percent / 100)}" height="12" rx="6" fill="#bc8cff" />'
    body += '</g>'

    # Skills section
    body += f'<g transform="translate(30, {skills_y})">'
    body += '<text y="0" style="font: 600 14px \'Segoe UI\', Arial, sans-serif; text-transform: uppercase;" fill="#c9d1d9">Skills</text>'
    col1_skills = skills[:5]
    col2_skills = skills[5:10]
    y_pos = 30
    for i in range(num_skill_rows):
        if i < len(col1_skills):
            s = col1_skills[i]
            bar_w = min(350 * (s.get('level', 0.0) / MAX_SKILL_LEVEL), 350)
            body += f'<g transform="translate(0, {y_pos + (i * 35)})"><text style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{html.escape(s.get("name"))}</text><text x="350" text-anchor="end" style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{s.get("level", 0.0):.2f}</text><rect y="8" width="350" height="6" rx="3" fill="#21262d" /><rect y="8" width="{bar_w}" height="6" rx="3" fill="#3fb950" /></g>'
        if i < len(col2_skills):
            s = col2_skills[i]
            bar_w = min(350 * (s.get('level', 0.0) / MAX_SKILL_LEVEL), 350)
            body += f'<g transform="translate(390, {y_pos + (i * 35)})"><text style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{html.escape(s.get("name"))}</text><text x="350" text-anchor="end" style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{s.get("level", 0.0):.2f}</text><rect y="8" width="350" height="6" rx="3" fill="#21262d" /><rect y="8" width="{bar_w}" height="6" rx="3" fill="#3fb950" /></g>'
    body += '</g>'

    # Projects section
    if in_progress_projects:
        body += f'<g transform="translate(30, {projects_y})">'
        body += '<text y="0" style="font: 600 14px \'Segoe UI\', Arial, sans-serif; text-transform: uppercase;" fill="#c9d1d9">Current Projects</text>'
        body += '<text y="30" style="font: 600 14px \'Segoe UI\', Arial, sans-serif;">'
        for i, p in enumerate(in_progress_projects):
            spacing = 'dx="25"' if i > 0 else ''
            body += f'<tspan {spacing} fill="#FFD140">★</tspan><tspan fill="#8b949e"> {html.escape(p["project"]["name"])}</tspan>'
        body += '</text>'
        body += '</g>'
    
    # Calculate final height
    height = projects_y + 60 if in_progress_projects else skills_y + 30 + (num_skill_rows * 35) + padding

    return body, height

def main():
    """Main function to run the process."""
    try:
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        user_response = requests.get(f"https://api.intra.42.fr/v2/users/{LOGIN}", headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        svg_body, card_height = generate_svg_body(user_data)
        
        # Assemble the final SVG
        svg_final = f'<svg width="{CARD_WIDTH}" height="{card_height}" viewBox="0 0 {CARD_WIDTH} {card_height}" fill="none" xmlns="http://www.w3.org/2000/svg">'
        svg_final += f'<rect width="{CARD_WIDTH}" height="{card_height}" rx="10" fill="transparent"/>'
        svg_final += svg_body
        svg_final += '</svg>'
        
        with open("progress.svg", "w") as f:
            f.write(svg_final)
        print("✅ SVG generated and written to progress.svg")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()