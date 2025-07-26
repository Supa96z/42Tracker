import os
import requests
import html
import sys

# --- CONFIGURATION ---
LOGIN = "abataill"
MAX_SKILL_LEVEL = 21.0 # The level at which a skill bar is considered 100%

# --- SVG STYLING ---
# Feel free to change these colors
STYLE = """
<style>
    .bg { fill: #1a1b26; }
    .title { font-size: 24px; font-weight: bold; fill: #c0caf5; font-family: 'Segoe UI', Arial, sans-serif; }
    .subtitle { font-size: 14px; font-weight: bold; fill: #a9b1d6; font-family: 'Segoe UI', Arial, sans-serif; }
    .text { font-size: 14px; fill: #a9b1d6; font-family: 'Segoe UI', Arial, sans-serif; }
    .bar-bg { fill: #414868; }
    .level-bar { fill: #7aa2f7; }
    .rncp-bar { fill: #bb9af7; }
    .skill-bar { fill: #9ece6a; }
</style>
"""

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
    """Generates the SVG content from user data."""
    # --- Data Processing ---
    cursus_data = next((c for c in data["cursus_users"] if c["cursus_id"] == 21), None)
    if not cursus_data:
        raise Exception("ERROR: Cursus ID 21 not found for this user.")

    level_float = cursus_data.get("level", 0.0)
    level_int = int(level_float)
    level_decimal_percent = (level_float - level_int)
    
    rncp_percent = (level_float / 21) * 100
    if rncp_percent > 100: rncp_percent = 100
    
    skills = sorted(cursus_data.get("skills", []), key=lambda x: x['level'], reverse=True)

    # --- SVG Building ---
    svg_parts = []
    svg_parts.append('<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append(STYLE)
    svg_parts.append('<rect width="100%" height="100%" class="bg"/>')
    svg_parts.append('<text x="30" y="50" class="title">My 42 Cursus Status</text>')
    
    # --- Level Section ---
    svg_parts.append(f'<text x="30" y="110" class="subtitle">CURRENT LEVEL</text>')
    svg_parts.append(f'<text x="30" y="145" font-size="28" font-weight="bold" fill="#7aa2f7">{level_float:.2f}</text>')
    svg_parts.append(f'<rect x="30" y="165" width="350" height="15" rx="7.5" class="bar-bg"/>')
    svg_parts.append(f'<rect x="30" y="165" width="{350 * level_decimal_percent}" height="15" rx="7.5" class="level-bar"/>')

    # --- RNCP Section ---
    svg_parts.append(f'<text x="30" y="230" class="subtitle">PROGRESS TOWARDS RNCP LVL 7 (LVL 21)</text>')
    svg_parts.append(f'<text x="30" y="265" font-size="28" font-weight="bold" fill="#bb9af7">{rncp_percent:.0f}%</text>')
    svg_parts.append(f'<rect x="30" y="285" width="350" height="15" rx="7.5" class="bar-bg"/>')
    svg_parts.append(f'<rect x="30" y="285" width="{350 * (rncp_percent / 100)}" height="15" rx="7.5" class="rncp-bar"/>')

    # --- Skills Section ---
    svg_parts.append('<text x="420" y="110" class="subtitle">SKILLS</text>')
    y_pos = 140
    for skill in skills:
        skill_name = html.escape(skill.get("name", "Unknown"))
        skill_level = skill.get("level", 0.0)
        bar_width = 350 * (skill_level / MAX_SKILL_LEVEL)
        
        svg_parts.append(f'<g transform="translate(420, {y_pos})">')
        svg_parts.append(f'    <text class="text">{skill_name}</text>')
        svg_parts.append(f'    <text class="text" x="350" text-anchor="end">{skill_level:.2f}</text>')
        svg_parts.append(f'    <rect y="10" width="350" height="8" rx="4" class="bar-bg"/>')
        svg_parts.append(f'    <rect y="10" width="{bar_width}" height="8" rx="4" class="skill-bar"/>')
        svg_parts.append(f'</g>')
        y_pos += 40

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

def main():
    """Main function to run the process."""
    try:
        print(f"--- Starting SVG Generation for user: {LOGIN} ---")
        token = get_token()
        
        headers = {"Authorization": f"Bearer {token}"}
        api_url = f"https://api.intra.42.fr/v2/users/{LOGIN}"
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        print("✅ API Data fetched successfully.")
        
        svg_content = generate_svg(user_data)
        print("✅ SVG content generated successfully.")
        
        with open("progress.svg", "w") as f:
            f.write(svg_content)
        print("✅ progress.svg file written successfully.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()