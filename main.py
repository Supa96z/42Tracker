import os
import requests
import html

def get_token():
    """
    Authenticates with the 42 API to get an access token.
    Credentials are read from environment variables.
    """
    API_UID = os.getenv("API_UID")
    API_SECRET = os.getenv("API_SECRET")
    TOKEN_URL = "https://api.intra.42.fr/oauth/token"

    if not API_UID or not API_SECRET:
        raise Exception("API_UID and API_SECRET environment variables must be set.")

    token_data = {
        "grant_type": "client_credentials",
        "client_id": API_UID,
        "client_secret": API_SECRET,
    }
    
    response = requests.post(TOKEN_URL, data=token_data)
    response.raise_for_status()
    return response.json()["access_token"]

def main():
    """Main function to fetch data and generate the SVG."""
    try:
        LOGIN = "abataill"
        
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # --- 1. DATA FETCHING ---
        api_url = f"https://api.intra.42.fr/v2/users/{LOGIN}"
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        
        # --- 2. DATA PROCESSING ---
        # Note: Index [1] is usually the main cursus. It might be [0] for some users.
        cursus_data = user_data["cursus_users"][1]
        
        user_level_float = cursus_data.get("level", 0.0)
        level_int = int(user_level_float)
        level_decimal = int((user_level_float - level_int) * 100)
        level_progress_width = 350 * (level_decimal / 100)
        
        rncp7_percentage = (user_level_float / 21) * 100
        if rncp7_percentage > 100: rncp7_percentage = 100
        rncp7_progress_width = 350 * (rncp7_percentage / 100)
        
        skills_data = cursus_data.get("skills", [])

        # --- 3. SVG GENERATION ---
        with open("template.svg", "r") as f:
            svg_content = f.read()

        svg_content = svg_content.replace("%%LEVEL_INT%%", str(level_int))
        svg_content = svg_content.replace("%%LEVEL_DECIMAL%%", f"{level_decimal:02d}")
        svg_content = svg_content.replace('id="level-progress-bar" width="0"', f'id="level-progress-bar" width="{level_progress_width}"')
        
        svg_content = svg_content.replace("%%RNCP7_PERCENT%%", str(int(rncp7_percentage)))
        svg_content = svg_content.replace('id="rncp7-progress-bar" width="0"', f'id="rncp7-progress-bar" width="{rncp7_progress_width}"')
        
        # Generate and inject the skills block
        skills_svg_block = ""
        y_pos = 140
        # Sort skills by level, highest first
        for skill in sorted(skills_data, key=lambda x: x['level'], reverse=True):
            # Escape the skill name to handle special characters like '&'
            skill_name = html.escape(skill["name"])
            skill_level = skill["level"]
            skill_progress_width = 350 * (skill_level / 100)
            
            skill_bar_svg = f"""<g transform="translate(420, {y_pos})">
                <text class="text">{skill_name}</text>
                <text class="text" x="350" text-anchor="end">{skill_level:.2f}%</text>
                <rect y="10" width="350" height="8" rx="4" class="bar-bg"/>
                <rect y="10" width="{skill_progress_width}" height="8" rx="4" class="skill-bar"/>
              </g>"""
            skills_svg_block += skill_bar_svg
            y_pos += 40
            
        svg_content = svg_content.replace("", skills_svg_block)

        with open("progress.svg", "w") as f:
            f.write(svg_content)
            
        print("✅ SVG generated successfully!")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data from API: {e}")
    except IndexError:
        print("❌ Error: Could not find cursus_users[1]. Try changing the index to [0].")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()