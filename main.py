import os
import requests
import html
import sys

# --- CONFIGURATION ---
LOGIN = "abataill"
MAX_SKILL_LEVEL = 21.0

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
    """Generates the SVG content from user data with inline styles."""
    # --- Data Processing ---
    cursus_data = next((c for c in data["cursus_users"] if c["cursus_id"] == 21), None)
    if not cursus_data:
        raise Exception("ERROR: Cursus ID 21 not found for this user.")

    level_float = cursus_data.get("level", 0.0)
    rncp_percent = min((level_float / 21) * 100, 100)
    skills = sorted(cursus_data.get("skills", []), key=lambda x: x['level'], reverse=True)

    # --- SVG Building ---
    svg_parts = []
    svg_parts.append('<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">')
    # Background
    svg_parts.append('<rect width="100%" height="100%" rx="10" style="fill: #1d1f21;" />')
    # Title
    svg_parts.append(f'<text x="30" y="40" style="font: 600 18px \'Segoe UI\', Arial, sans-serif; fill: #c5c8c6;">42 Cursus Status for {LOGIN}</text>')

    # --- Left Side: Level & RNCP ---
    svg_parts.append('<g transform="translate(30, 80)">')
    # Level
    svg_parts.append('<text y="20" style="font: 600 12px \'Segoe UI\', Arial, sans-serif; fill: #81a2be; text-transform: uppercase;">Current Level</text>')
    svg_parts.append(f'<text y="55" style="font: 700 28px \'Segoe UI\', Arial, sans-serif; fill: #81a2be;">{level_float:.2f}</text>')
    svg_parts.append(f'<rect y="75" width="350" height="15" rx="7.5" style="fill: #282a2e;" />')
    svg_parts.append(f'<rect y="75" width="{350 * (level_float - int(level_float))}" height="15" rx="7.5" style="fill: #81a2be;" />')
    # RNCP
    svg_parts.append('<text y="140" style="font: 600 12px \'Segoe UI\', Arial, sans-serif; fill: #b294bb; text-transform: uppercase;">Progress to RNCP Level 7</text>')
    svg_parts.append(f'<text y="175" style="font: 700 28px \'Segoe UI\', Arial, sans-serif; fill: #b294bb;">{rncp_percent:.0f}%</text>')
    svg_parts.append(f'<rect y="195" width="350" height="15" rx="7.5" style="fill: #282a2e;" />')
    svg_parts.append(f'<rect y="195" width="{350 * (rncp_percent / 100)}" height="15" rx="7.5" style="fill: #b294bb;" />')
    svg_parts.append('</g>')

    # --- Right Side: Skills ---
    skills_height = len(skills) * 40
    y_offset = 80 + (250 - skills_height) / 2
    svg_parts.append(f'<g transform="translate(420, {y_offset})">')
    svg_parts.append('<text y="0" style="font: 600 12px \'Segoe UI\', Arial, sans-serif; fill: #b5bd68; text-transform: uppercase;">Skills</text>')
    y_pos = 25
    for skill in skills:
        skill_name = html.escape(skill.get("name", "Unknown"))
        skill_level = skill.get("level", 0.0)
        bar_width = min(350 * (skill_level / MAX_SKILL_LEVEL), 350)
        
        svg_parts.append(f'<g transform="translate(0, {y_pos})">')
        svg_parts.append(f'    <text style="font: 400 14px \'Segoe UI\', Arial, sans-serif; fill: #c5c8c6;">{skill_name}</text>')
        svg_parts.append(f'    <text x="350" text-anchor="end" style="font: 400 14px \'Segoe UI\', Arial, sans-serif; fill: #c5c8c6;">{skill_level:.2f}</text>')
        svg_parts.append(f'    <rect y="10" width="350" height="8" rx="4" style="fill: #282a2e;" />')
        svg_parts.append(f'    <rect y="10" width="{bar_width}" height="8" rx="4" style="fill: #b5bd68;" />')
        svg_parts.append(f'</g>')
        y_pos += 40
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