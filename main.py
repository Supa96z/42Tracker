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

def generate_svg(data):
    """Generates a complete, adaptive SVG from user data with a robust layout."""
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

    # --- LAYOUT & HEIGHT CALCULATION ---
    # Define fixed heights and gaps for a consistent layout
    padding = 25
    section_gap = 5
    header_section_height = 80
    
    num_skill_rows = (len(skills[:10]) + 1) // 2
    skills_section_height = 30 + (num_skill_rows * 35) # Title + rows
    
    projects_section_height = 0
    if in_progress_projects:
        projects_section_height = 50 # Title + one row of projects
    
    # Calculate total height based on content
    card_height = header_section_height + section_gap + skills_section_height
    if in_progress_projects:
        card_height += section_gap + projects_section_height
    card_height += padding - 20

    # --- SVG Building ---
    svg_parts = []
    svg_parts.append(f'<svg width="{CARD_WIDTH}" height="{card_height}" viewBox="0 0 {CARD_WIDTH} {card_height}" fill="none" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append(f'<rect width="{CARD_WIDTH}" height="{card_height}" rx="10" fill="transparent"/>')
    
    # --- Top Row: Level & RNCP ---
    svg_parts.append(f'<g transform="translate(30, {padding})">')
    # COMBINED TITLE AND VALUE
    svg_parts.append(f'<text y="25" style="font: 600 18px \'Segoe UI\', Arial, sans-serif;" fill="#88c0d0">LEVEL {level_float:.2f}</text>')
    svg_parts.append(f'<rect y="40" width="350" height="12" rx="6" fill="#21262d" />')
    svg_parts.append(f'<rect y="40" width="{350 * (level_float - int(level_float))}" height="12" rx="6" fill="#88c0d0" />')
    svg_parts.append('</g>')
    
    svg_parts.append(f'<g transform="translate(420, {padding})">')
    # COMBINED TITLE AND VALUE
    svg_parts.append(f'<text y="25" style="font: 600 18px \'Segoe UI\', Arial, sans-serif;" fill="#b48ead">{rncp_percent:.0f}% TOWARDS RNCP 7</text>')
    svg_parts.append(f'<rect y="40" width="350" height="12" rx="6" fill="#21262d" />')
    svg_parts.append(f'<rect y="40" width="{350 * (rncp_percent / 100)}" height="12" rx="6" fill="#b48ead" />')
    svg_parts.append('</g>')


    # --- Middle Section: Skills ---
    skills_y_start = padding + header_section_height + section_gap
    svg_parts.append(f'<g transform="translate(30, {skills_y_start})">')
    svg_parts.append('<text y="0" style="font: 600 14px \'Segoe UI\', Arial, sans-serif; text-transform: uppercase;" fill="#a3be8c">Skills</text>')
    
    col1_skills = skills[:5]
    col2_skills = skills[5:10]
    y_pos = 20
    skill_row_height = 35
    for i in range(num_skill_rows):
        if i < len(col1_skills):
            skill = col1_skills[i]
            skill_name = html.escape(skill.get("name", "Unknown"))
            skill_level = skill.get("level", 0.0)
            bar_width = min(350 * (skill_level / MAX_SKILL_LEVEL), 350)
            svg_parts.append(f'<g transform="translate(0, {y_pos + (i * skill_row_height)})"><text style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{skill_name}</text><text x="350" text-anchor="end" style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{skill_level:.2f}</text><rect y="8" width="350" height="6" rx="3" fill="#21262d" /><rect y="8" width="{bar_width}" height="6" rx="3" fill="#a3be8c" /></g>')
        if i < len(col2_skills):
            skill = col2_skills[i]
            skill_name = html.escape(skill.get("name", "Unknown"))
            skill_level = skill.get("level", 0.0)
            bar_width = min(350 * (skill_level / MAX_SKILL_LEVEL), 350)
            svg_parts.append(f'<g transform="translate(390, {y_pos + (i * skill_row_height)})"><text style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{skill_name}</text><text x="350" text-anchor="end" style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{skill_level:.2f}</text><rect y="8" width="350" height="6" rx="3" fill="#21262d" /><rect y="8" width="{bar_width}" height="6" rx="3" fill="#a3be8c" /></g>')
    svg_parts.append('</g>')

    # --- Bottom Section: Current Projects ---
    if in_progress_projects:
        projects_y_start = skills_y_start + skills_section_height + section_gap - 5
        svg_parts.append(f'<g transform="translate(30, {projects_y_start})">')
        svg_parts.append('<text y="0" style="font: 600 14px \'Segoe UI\', Arial, sans-serif; text-transform: uppercase;" fill="#ebcb8b">Current Projects</text>')
        
        projects_line = '<text y="25" style="font: 400 14px \'Segoe UI\', Arial, sans-serif;">'
        for i, project in enumerate(in_progress_projects):
            project_name = html.escape(project['project']['name'])
            spacing = 'dx="25"' if i > 0 else ''
            projects_line += f'<tspan {spacing} fill="#ebcb8b">★</tspan><tspan fill="#c9d1d9"> {project_name}</tspan>'
        projects_line += '</text>'
        
        svg_parts.append(projects_line)
        svg_parts.append('</g>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

def main():
    """Main function to run the process."""
    try:
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        user_response = requests.get(f"https://api.intra.42.fr/v2/users/{LOGIN}", headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        svg_content = generate_svg(user_data)
        
        with open("progress.svg", "w") as f:
            f.write(svg_content)
        print("✅ SVG generated and written to progress.svg")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()