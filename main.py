import os
import requests
import html
import sys

def get_token():
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

def main():
    LOGIN = "abataill"
    print(f"--- Starting SVG Generation for user: {LOGIN} ---")

    token = get_token()
    print("✅ API Token received successfully.")

    headers = {"Authorization": f"Bearer {token}"}
    api_url = f"https://api.intra.42.fr/v2/users/{LOGIN}"
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    user_data = response.json()
    print("✅ User data fetched successfully.")

    cursus_data = next((c for c in user_data["cursus_users"] if c["cursus_id"] == 21), None)
    if not cursus_data:
        raise Exception("ERROR: Cursus ID 21 not found for this user.")
    print(f"✅ Found Cursus data: {cursus_data['cursus']['name']}")

    user_level_float = cursus_data.get("level", 0.0)
    level_int = int(user_level_float)
    level_decimal = int(round((user_level_float - level_int) * 100))
    print(f"-> Level processed: {user_level_float}")

    skills_data = cursus_data.get("skills", [])
    print(f"-> Found {len(skills_data)} skills.")

    with open("template.svg", "r") as f:
        svg_content = f.read()

    # Perform replacements
    svg_content = svg_content.replace("%%LEVEL_INT%%", str(level_int))
    svg_content = svg_content.replace("%%LEVEL_DECIMAL%%", f"{level_decimal:02d}")
    # Add more replacements...

    skills_svg_block = ""
    y_pos = 140
    for skill in sorted(skills_data, key=lambda x: x['level'], reverse=True):
        skill_name = html.escape(skill.get("name", "Unknown Skill"))
        skill_level = skill.get("level", 0.0)
        skill_progress_width = 350 * (skill_level / 21)

        skills_svg_block += f"""<g transform="translate(420, {y_pos})">
            <text class="text">{skill_name}</text>
            <text class="text" x="350" text-anchor="end">{skill_level:.2f}</text>
            <rect y="10" width="350" height="8" rx="4" class="bar-bg"/>
            <rect y="10" width="{skill_progress_width}" height="8" rx="4" class="skill-bar"/>
        </g>"""
        y_pos += 40

    svg_content = svg_content.replace("", skills_svg_block)
    print("✅ SVG content generated.")

    with open("progress.svg", "w") as f:
        f.write(svg_content)
    print("✅ progress.svg file written successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)