# scoreboard_layout.py
import os
import json

BASE_DIR = os.path.dirname(__file__)

with open(os.path.join(BASE_DIR, "data", "w64h32.json"), "r") as f:
    LAYOUT = json.load(f)

def get_layout(*keys):
    """
    e.g. get_layout("bases","1B") => { "x":56, "y":20, "size":6 }
    if missing, returns {}.
    """
    ref = LAYOUT
    for k in keys:
        if k in ref:
            ref = ref[k]
        else:
            return {}
    return ref if isinstance(ref, dict) else {}

def get_default_font():
    """
    e.g. LAYOUT["defaults"]["font_name"] => "4x6"
    """
    defaults = LAYOUT.get("defaults", {})
    return defaults.get("font_name", "4x6")
