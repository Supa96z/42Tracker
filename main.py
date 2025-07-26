import os
import requests
import html
import sys

# --- CONFIGURATION ---
LOGIN = "abataill"
# The level at which a skill is considered maxed out for the progress bar
MAX_SKILL_LEVEL = 21.0
# The width of the SVG
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
    # Base height + space for each skill
    card_height = 200 + (len(skills) * 35)

    # --- SVG Building with inline attributes for maximum compatibility ---
    svg_parts = []
    # Header
    svg_parts.append(f'<svg width="{CARD_WIDTH}" height="{card_height}" viewBox="0 0 {CARD_WIDTH} {card_height}" fill="none" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append(f'<rect width="{CARD_WIDTH}" height="{card_height}" rx="10" fill="#1d1f21"/>')
    # Title
    svg_parts.append(f'<text x="30" y="45" font-family="\'Segoe UI\', Arial, sans-serif" font-size="20" font-weight="600" fill="#c5c8c6">42 Cursus Status: {LOGIN}</text>')
    
    # --- Left Side: Level & RNCP ---
    svg_parts.append('<g transform="translate(30, 80)">')
    # Level
    svg_parts.append('<text y="0" font-family="\'Segoe UI\', Arial, sans-serif" font-size="14" font-weight="600" fill="#81a2be" style="text-transform: uppercase;">Current Level</text>')
    svg_parts.append(f'<text y="35" font-family="\'Segoe UI\', Arial, sans-serif" font-size="28" font-weight="700" fill="#81a2be">{level_float:.2f}</text>')
    svg_parts.append(f'<rect y="50" width="350" height="12" rx="6" fill="#282a2e" />')
    svg_parts.append(f'<rect y="50" width="{350 * (level_float - int(level_float))}" height="12" rx="6" fill="#81a2be" />')
    
    # RNCP
    svg_parts.append('<text y="95" font-family="\'Segoe UI\', Arial, sans-serif" font-size="14" font-weight="600" fill="#b294bb" style="text-transform: uppercase;">Progress to RNCP Level 7</text>')
    svg_parts.append(f'<text y="130" font-family="\'Segoe UI\', Arial, sans-serif" font-size="28" font-weight="700" fill="#b294bb">{rncp_percent:.0f}%</text>')
    svg_parts.append(f'<rect y="145" width="350" height="12" rx="6" fill="#282a2e" />')
    svg_parts.append(f'<rect y="145" width="{350 * (rncp_percent / 100)}" height="12" rx="6" fill="#b294bb" />')
    svg_parts.append('</g>')

    # --- Right Side: Skills ---
    svg_parts.append('<g transform="translate(420, 80)">')
    svg_parts.append('<text y="0" font-family="\'Segoe UI\', Arial, sans-serif" font-size="14" font-weight="600" fill="#b5bd68" style="text-transform: uppercase;">Skills</text>')
    y_pos = 30
    for skill in skills:
        skill_name = html.escape(skill.get("name", "Unknown"))
        skill_level = skill.get("level", 0.0)
        bar_width = min(350 * (skill_level / MAX_SKILL_LEVEL), 350)
        
        svg_parts.append(f'<g transform="translate(0, {y_pos})">')
        svg_parts.append(f'    <text font-family="\'Segoe UI\', Arial, sans-serif" font-size="14" fill="#c5c8c6">{skill_name}</text>')
        svg_parts.append(f'    <text x="350" text-anchor="end" font-family="\'Segoe UI\', Arial, sans-serif" font-size="14" fill="#c5c8c6">{skill_level:.2f}</text>')
        svg_parts.append(f'    <rect y="10" width="350" height="8" rx="4" fill="#282a2e" />')
        svg_parts.append(f'    <rect y="10" width="{bar_width}" height="8" rx="4" fill="#b5bd68" />')
        svg_parts.append(f'</g>')
        y_pos += 35
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