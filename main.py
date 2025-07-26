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
    """Generates a complete, adaptive SVG from user data."""
    # --- Data Processing ---
    cursus_data = next((c for c in data["cursus_users"] if c["cursus_id"] == 21), None)
    if not cursus_data:
        raise Exception("ERROR: Cursus ID 21 not found for this user.")

    level_float = cursus_data.get("level", 0.0)
    rncp_percent = min((level_float / 21) * 100, 100)
    skills = sorted(cursus_data.get("skills", []), key=lambda x: x['level'], reverse=True)

    # --- DYNAMIC HEIGHT CALCULATION ---
    header_height = 130
    skills_header_height = 40
    # Determine the number of rows needed for the skills section (2 skills per row)
    num_skill_rows = (len(skills[:10]) + 1) // 2
    row_height = 35
    bottom_padding = 15 # Reduced padding for a snug fit
    card_height = header_height + skills_header_height + (num_skill_rows * row_height) + bottom_padding

    # --- SVG Building ---
    svg_parts = []
    svg_parts.append(f'<svg width="{CARD_WIDTH}" height="{card_height}" viewBox="0 0 {CARD_WIDTH} {card_height}" fill="none" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append(f'<rect width="{CARD_WIDTH}" height="{card_height}" rx="10" fill="transparent"/>')
    
    # --- Top Row: Level & RNCP ---
    svg_parts.append('<g transform="translate(30, 30)">')
    svg_parts.append('<text y="0" style="font: 600 14px \'Segoe UI\', Arial, sans-serif; text-transform: uppercase;" fill="#c9d1d9">Current Level</text>')
    svg_parts.append(f'<text y="35" style="font: 700 28px \'Segoe UI\', Arial, sans-serif;" fill="#58a6ff">{level_float:.2f}</text>')
    svg_parts.append(f'<rect y="50" width="350" height="12" rx="6" fill="#21262d" />')
    svg_parts.append(f'<rect y="50" width="{350 * (level_float - int(level_float))}" height="12" rx="6" fill="#58a6ff" />')
    svg_parts.append('</g>')
    svg_parts.append('<g transform="translate(420, 30)">')
    svg_parts.append('<text y="0" style="font: 600 14px \'Segoe UI\', Arial, sans-serif; text-transform: uppercase;" fill="#c9d1d9">Progress to RNCP Level 7</text>')
    svg_parts.append(f'<text y="35" style="font: 700 28px \'Segoe UI\', Arial, sans-serif;" fill="#bc8cff">{rncp_percent:.0f}%</text>')
    svg_parts.append(f'<rect y="50" width="350" height="12" rx="6" fill="#21262d" />')
    svg_parts.append(f'<rect y="50" width="{350 * (rncp_percent / 100)}" height="12" rx="6" fill="#bc8cff" />')
    svg_parts.append('</g>')

    # --- Bottom Section: Skills ---
    svg_parts.append(f'<g transform="translate(30, {header_height})">')
    svg_parts.append('<text y="0" style="font: 600 14px \'Segoe UI\', Arial, sans-serif; text-transform: uppercase;" fill="#c9d1d9">Skills</text>')
    
    col1_skills = skills[:5]
    col2_skills = skills[5:10]
    y_pos = 30
    for i in range(num_skill_rows):
        # Column 1
        if i < len(col1_skills):
            skill = col1_skills[i]
            skill_name = html.escape(skill.get("name", "Unknown"))
            skill_level = skill.get("level", 0.0)
            bar_width = min(350 * (skill_level / MAX_SKILL_LEVEL), 350)
            
            svg_parts.append(f'<g transform="translate(0, {y_pos + (i * row_height)})">')
            svg_parts.append(f'    <text style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{skill_name}</text>')
            svg_parts.append(f'    <text x="350" text-anchor="end" style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{skill_level:.2f}</text>')
            svg_parts.append(f'    <rect y="8" width="350" height="6" rx="3" fill="#21262d" />')
            svg_parts.append(f'    <rect y="8" width="{bar_width}" height="6" rx="3" fill="#3fb950" />')
            svg_parts.append(f'</g>')
        # Column 2
        if i < len(col2_skills):
            skill = col2_skills[i]
            skill_name = html.escape(skill.get("name", "Unknown"))
            skill_level = skill.get("level", 0.0)
            bar_width = min(350 * (skill_level / MAX_SKILL_LEVEL), 350)
            
            svg_parts.append(f'<g transform="translate(390, {y_pos + (i * row_height)})">')
            svg_parts.append(f'    <text style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{skill_name}</text>')
            svg_parts.append(f'    <text x="350" text-anchor="end" style="font: 400 12px \'Segoe UI\', Arial, sans-serif;" fill="#8b949e">{skill_level:.2f}</text>')
            svg_parts.append(f'    <rect y="8" width="350" height="6" rx="3" fill="#21262d" />')
            svg_parts.append(f'    <rect y="8" width="{bar_width}" height="6" rx="3" fill="#3fb950" />')
            svg_parts.append(f'</g>')

    svg_parts.append('</g>')
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

def main():
    """Main function to run the process."""
    try:
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        api_url = f"https://api.intra.42.fr/v2/users/{LOGIN}"
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        
        svg_content = generate_svg(user_data)
        
        with open("progress.svg", "w") as f:
            f.write(svg_content)
        print("✅ SVG generated and written to progress.svg")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()