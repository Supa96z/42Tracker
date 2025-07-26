import os
import requests

# --- 1. AUTHENTICATION ---
# Get credentials securely from GitHub Secrets
API_UID = os.getenv("API_UID")
API_SECRET = os.getenv("API_SECRET")
LOGIN = "abataill" # Your 42 username

# The endpoint to get an API token
TOKEN_URL = "https://api.intra.42.fr/oauth/token"

# Data to send for authentication
token_data = {
    "grant_type": "client_credentials",
    "client_id": API_UID,
    "client_secret": API_SECRET,
}

try:
    # Get the access token
    response = requests.post(TOKEN_URL, data=token_data)
    response.raise_for_status() # Raise an exception for bad status codes
    access_token = response.json()["access_token"]
    print("Successfully authenticated with 42 API.")
except requests.exceptions.RequestException as e:
    print(f"Error authenticating: {e}")
    exit(1)


# --- 2. DATA FETCHING ---
# Headers for authenticated requests
headers = {"Authorization": f"Bearer {access_token}"}

try:
    # Fetch user data
    user_data_response = requests.get(f"https://api.intra.42.fr/v2/users/{LOGIN}", headers=headers)
    user_data_response.raise_for_status()
    user_data = user_data_response.json()
    print("Successfully fetched user data.")
except requests.exceptions.RequestException as e:
    print(f"Error fetching user data: {e}")
    exit(1)


# --- 3. DATA PROCESSING ---

# Find the main 42cursus data (this is more robust than using a fixed index)
main_cursus_data = None
for cursus in user_data.get("cursus_users", []):
    if cursus.get("cursus_id") == 21: # 21 is the ID for the main 42 Cursus
        main_cursus_data = cursus
        break

if not main_cursus_data:
    print("Could not find main 42 Cursus data for the user.")
    exit(1)

# --- Process Level Data ---
user_level_float = main_cursus_data.get("level", 0.0)
level_int = int(user_level_float)
level_decimal = int((user_level_float - level_int) * 100)
level_progress_width = 350 * (level_decimal / 100) # Max bar width is 350px

# --- Process RNCP7 (Level 21) Progress ---
rncp7_percentage = (user_level_float / 21) * 100
if rncp7_percentage > 100:
    rncp7_percentage = 100
rncp7_progress_width = 350 * (rncp7_percentage / 100) # Max bar width is 350px

# --- Process Skills Data ---
skills_data = main_cursus_data.get("skills", [])
skills_svg_block = ""
current_y_position = 140 # Starting Y position for the first skill

for skill in sorted(skills_data, key=lambda x: x['level'], reverse=True): # Sort skills by level
    skill_name = skill["name"]
    skill_level = skill["level"]
    # Calculate width of the bar for this skill (max width 350px)
    skill_progress_width = 350 * (skill_level / 20) # Assuming max skill level is ~20 for scaling
    if skill_progress_width > 350:
        skill_progress_width = 350

    # Create the SVG code for a single skill bar
    skill_bar_svg = f"""
      <g transform="translate(420, {current_y_position})">
        <text class="text">{skill_name}</text>
        <text class="text" x="350" text-anchor="end">{skill_level:.2f}</text>
        <rect y="10" width="350" height="8" rx="4" class="bar-bg"/>
        <rect y="10" width="{skill_progress_width}" height="8" rx="4" class="skill-bar"/>
      </g>
    """
    skills_svg_block += skill_bar_svg
    current_y_position += 40 # Move down for the next skill


# --- 4. SVG GENERATION ---
try:
    # Read a blank template file
    with open("template.svg", "r") as f:
        svg_content = f.read()
except FileNotFoundError:
    print("Error: template.svg not found. Make sure the file exists.")
    exit(1)


# Replace placeholders in the template with your data
svg_content = svg_content.replace("%%LEVEL_INT%%", str(level_int))
svg_content = svg_content.replace("%%LEVEL_DECIMAL%%", f"{level_decimal:02d}")
svg_content = svg_content.replace('id="level-progress-bar" width="0"', f'id="level-progress-bar" width="{level_progress_width}"')

svg_content = svg_content.replace("%%RNCP7_PERCENT%%", str(int(rncp7_percentage)))
svg_content = svg_content.replace('id="rncp7-progress-bar" width="0"', f'id="rncp7-progress-bar" width="{rncp7_progress_width}"')

# Replace the skills placeholder with the dynamically generated block
svg_content = svg_content.replace("<!-- SKILLS_PLACEHOLDER -->", skills_svg_block)


# Write the new content to the final SVG file
with open("progress.svg", "w") as f:
    f.write(svg_content)

print("Successfully generated progress.svg!")
