# scoreboard_colors.py

import os
import json
from rgbmatrix import graphics

BASE_DIR = os.path.dirname(__file__)

# Load scoreboard color data (scoreboard.json)
with open(os.path.join(BASE_DIR, "data", "scoreboard.json"), "r") as f:
    SB_COLORS = json.load(f)

# Load team color data (teams.json)
with open(os.path.join(BASE_DIR, "data", "teams.json"), "r") as f:
    TEAM_COLORS = json.load(f)

def rgb_obj_to_color(obj):
    """Given a dict { 'r':..., 'g':..., 'b':... } -> return a graphics.Color."""
    return graphics.Color(obj["r"], obj["g"], obj["b"])

def get_scoreboard_color(*keys):
    """
    Look up color(s) in scoreboard.json by keys path, e.g.:
      get_scoreboard_color("bases","1B")
    If not found, fallback to scoreboard["default"]["text"] or white.
    """
    ref = SB_COLORS
    for k in keys:
        if k in ref:
            ref = ref[k]
        else:
            # fallback to scoreboard["default"]["text"]
            return get_scoreboard_color("default", "text")
    # If the final 'ref' is a dict with r,g,b, convert to graphics.Color
    if isinstance(ref, dict) and "r" in ref:
        return rgb_obj_to_color(ref)
    return graphics.Color(255, 255, 255)

###############################################
# TEAM COLOR LOOKUPS
###############################################

def get_team_text_color(team_code):
    """
    Always returns the 'home' color from teams.json for the specified team_code.
    If that team_code is missing, fallback to the 'default' entry or pure white.
    """
    team_info = TEAM_COLORS.get(team_code)
    if not team_info:
        # fallback to 'default' if team_code not found
        team_info = TEAM_COLORS.get("default", {})
    # get the home color
    home_obj = team_info.get("home")
    home_obj = {"r": 255, "g": 255, "b": 255}
    if not home_obj:
        # fallback to something safe if missing
        home_obj = {"r": 255, "g": 255, "b": 255}
    return rgb_obj_to_color(home_obj)

def get_team_background_color(team_code):
    """
    Always returns the 'accent' color from teams.json for the specified team_code.
    If accent is missing or the code doesn't exist, fallback to the default accent or white.
    """
    team_info = TEAM_COLORS.get(team_code)
    if not team_info:
        # fallback to 'default' if team_code not found
        team_info = TEAM_COLORS.get("default", {})
    accent_obj = team_info.get("accent")
    if not accent_obj:
        # fallback if accent missing
        accent_obj = {"r": 255, "g": 255, "b": 255}
    return rgb_obj_to_color(accent_obj)
