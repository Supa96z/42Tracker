import os
import requests
import html
import sys

# --- CONFIGURATION ---
LOGIN = "abataill"
# The level at which a skill is considered maxed out for the progress bar
MAX_SKILL_LEVEL = 21.0
# SVG Dimensions
SVG_WIDTH = 800
SVG_HEIGHT = 280 # Made thinner

# --- STYLING (Feel free to change colors) ---
STYLE = """
<style>
    .bg {{ fill: #1d1f21; }}
    .title {{ font: 600 18px 'Segoe UI', Arial, sans-serif; fill: #c5c8c6; }}
    .text {{ font: 400 14px 'Segoe UI', Arial, sans-serif; fill: #c5c8c6; }}
    .subtitle {{ font: 600 12px 'Segoe UI', Arial, sans-serif; fill: #81a2be; text-transform: uppercase; }}
    .bar-bg {{ fill: #282a2e; }}
    .level-bar {{ fill: #81a2be; }}
    .rncp-bar {{ fill: #b294bb; }}
    .skill-bar {{ fill: #b5bd68; }}
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
    
    rncp_percent = (level_float / 21) * 100
    if rncp_percent > 100: rncp_percent = 100
    
    skills = sorted(cursus_data.get("skills", []), key=lambda x: x['level'], reverse=True)

    # --- SVG Building ---
    # The order is important: background first, then text and elements on top.
    svg_parts = []
    svg_parts.append(f'<svg width="{SVG_WIDTH}" height="{SVG_HEIGHT}" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append(STYLE)
    svg_parts.append('<rect width="100%" height="100%" rx="10" class="bg"/>') # Background drawn first
    
    svg_parts.append(f'<text x="30" y="40" class="title">42 Cursus Status for {LOGIN}</text>')
    
    # --- Level & RNCP Section (Left Side) ---
    svg_parts.append('<g transform="translate(30, 80)">')
    svg_parts.append(f'<text y="20" class="subtitle">Current Level</text>')
    svg_parts.append(f'<text y="55" font-size="28" font-weight="bold" class="level-bar">{level_float:.2f}</text>')
    svg_parts.append(f'<rect y="75" width="350" height="15" rx="7.5" class="bar-bg"/>')
    svg_parts.append(f'<rect y="75" width="{350 * (level_float - int(level_float))}" height="15" rx="7.5" class="level-bar"/>')
    svg_parts.append('</g>')

    # --- Skills Section (Right Side) ---
    svg_parts.append('<g transform="translate(420, 80)">')
    svg_parts.append('<text y="20" class="subtitle">Skills</text>')
    y_pos = 45 # Start position for the first skill bar
    for skill in skills[:4]: # Limit to top 4 skills to fit in the thinner design
        skill_name = html.escape(skill.get("name", "Unknown"))
        skill_level = skill.get("level", 0.0)
        bar_width = 350 * (skill_level / MAX_SKILL_LEVEL)
        if bar_width > 350: bar_width = 350

        svg_parts.append(f'<g transform="translate(0, {y_pos})">')
        svg_parts.append(f'    <text class="text">{skill_name}</text>')
        svg_parts.append(f'    <text class="text" x="350" text-anchor="end">{skill_level:.2f}</text>')
        svg_parts.append(f'    <rect y="10" width="350" height="8" rx="4" class="bar-bg"/>')
        svg_parts.append(f'    <rect y="10" width="{bar_width}" height="8" rx="4" class="skill-bar"/>')
        svg_parts.append(f'</g>')
        y_pos += 45
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
        print("✅ Polished progress.svg file written successfully.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()