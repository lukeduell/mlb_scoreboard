# scoreboard_draw.py

from rgbmatrix import graphics
import pytz
import datetime
from scoreboard_layout import get_layout
from scoreboard_colors import (
    get_scoreboard_color,
    get_team_text_color,
    get_team_background_color
)

def fill_rect(canvas, x, y, w, h, color):
    for yy in range(h):
        for xx in range(w):
            canvas.SetPixel(x + xx, y + yy, color.red, color.green, color.blue)
            
def convert_start_time_to_est(time_str):
    """
    Given a time string in the format "H:MM AM/PM" (assumed to be in UTC)
    and using today's date, convert it to US/Eastern time and return it
    formatted as "H:MM AM/PM". If time_str is "TBD", returns "TBD".
    """
    if time_str == "TBD":
        return time_str

    # Get today's date in UTC
    today = datetime.datetime.utcnow().date()
    # Combine today's date with the provided time string
    # For example, "2023-09-25 1:40 AM"
    try:
        dt_naive = datetime.datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %I:%M %p")
    except ValueError:
        return "TBD"
    # Localize the naive datetime as UTC
    dt_utc = pytz.utc.localize(dt_naive)
    # Convert to US/Eastern
    est = pytz.timezone("US/Eastern")
    dt_est = dt_utc.astimezone(est)
    # Format the time without a leading zero on the hour (Unix-only; on Windows use "%#I:%M %p")
    return dt_est.strftime("%-I:%M %p")

def draw_count(canvas, font, game_data):
    layout_info = get_layout("batter_count")
    x = layout_info.get("x", 30)
    y = layout_info.get("y", 30)

    count_col = get_scoreboard_color("batter_count")
    balls = game_data.get("balls", 0)
    strikes = game_data.get("strikes", 0)
    count_str = f"{balls}-{strikes}"

    graphics.DrawText(canvas, font, x, y, count_col, count_str)

def draw_bases(canvas, game_data):
    runners_on = game_data.get("runners_on", [])
    for base_key in ["1B", "2B", "3B"]:
        base_layout = get_layout("bases", base_key)
        if not base_layout:
            continue
        x = base_layout.get("x", 0)
        y = base_layout.get("y", 0)
        size = base_layout.get("size", 4)

        base_color = get_scoreboard_color("bases", base_key)
        fill = (base_key in runners_on)
        draw_base_square(canvas, x, y, size, base_color, fill)

def draw_base_square(canvas, x, y, size, color_empty, filled):
    # If runner is on base, we might do a different fill color
    fill_color = color_empty if not filled else graphics.Color(255, 0, 0)
    for dy in range(size):
        for dx in range(size):
            canvas.SetPixel(x + dx, y + dy, fill_color.red, fill_color.green, fill_color.blue)

def draw_outs(canvas, game_data):
    out_count = game_data.get("outs", 0)
    for i_str in ["1", "2", "3"]:
        out_layout = get_layout("outs", i_str)
        if not out_layout:
            continue
        x = out_layout["x"]
        y = out_layout["y"]
        size = out_layout["size"]

        outline_col = get_scoreboard_color("outs", i_str)
        fill_col = get_scoreboard_color("outs", "fill", i_str)
        fill_it = (out_count >= int(i_str))
        draw_out_box(canvas, x, y, size, outline_col, fill_col if fill_it else None)

def draw_out_box(canvas, x, y, size, outline_color, fill_color=None):
    # Fill first if we have a fill color
    if fill_color:
        for dy in range(size):
            for dx in range(size):
                canvas.SetPixel(x + dx, y + dy, fill_color.red, fill_color.green, fill_color.blue)
    # Then outline
    for dx in range(size):
        canvas.SetPixel(x + dx, y, outline_color.red, outline_color.green, outline_color.blue)
        canvas.SetPixel(x + dx, y + size - 1, outline_color.red, outline_color.green, outline_color.blue)
    for dy in range(size):
        canvas.SetPixel(x, y + dy, outline_color.red, outline_color.green, outline_color.blue)
        canvas.SetPixel(x + size - 1, y + dy, outline_color.red, outline_color.green, outline_color.blue)

def draw_inning_arrow(canvas, font, game_data):
    inning_layout = get_layout("inning", "number")
    arrow_layout  = get_layout("inning", "arrow")
    if not inning_layout or not arrow_layout:
        return

    x_num = inning_layout.get("x", 32)
    y_num = inning_layout.get("y", 20)
    is_top = game_data.get("is_top_inning", True)
    arrow_size = arrow_layout.get("size", 3)

    arrow_col = get_scoreboard_color("inning", "arrow", "up" if is_top else "down")

    # offsets
    off_x = arrow_layout["up"]["x_offset"] if is_top else arrow_layout["down"]["x_offset"]
    off_y = arrow_layout["up"]["y_offset"] if is_top else arrow_layout["down"]["y_offset"]

    arrow_x = x_num + off_x
    arrow_y = y_num + off_y
    draw_small_arrow(canvas, arrow_x, arrow_y, arrow_size, arrow_col,
                     direction="up" if is_top else "down")

    # Draw the inning number
    inn_col = get_scoreboard_color("inning", "number")
    inn_str = str(game_data.get("inning", 0))
    graphics.DrawText(canvas, font, x_num, y_num, inn_col, inn_str)

def draw_small_arrow(canvas, x, y, size, color, direction="up"):
    if direction == "up":
        # Arrow tip
        canvas.SetPixel(x + 1, y, color.red, color.green, color.blue)
        # Row below
        canvas.SetPixel(x,     y + 1, color.red, color.green, color.blue)
        canvas.SetPixel(x + 1, y + 1, color.red, color.green, color.blue)
        canvas.SetPixel(x + 2, y + 1, color.red, color.green, color.blue)
    else:
        # down arrow
        canvas.SetPixel(x,     y, color.red, color.green, color.blue)
        canvas.SetPixel(x + 1, y, color.red, color.green, color.blue)
        canvas.SetPixel(x + 2, y, color.red, color.green, color.blue)
        canvas.SetPixel(x + 1, y + 1, color.red, color.green, color.blue)

def draw_teams_and_score(canvas, font, game_data):
    """
    Adds the team record to the right of each team's code, e.g. "DET (11-0)"
    """
    teams_conf = get_layout("teams")
    if not teams_conf:
        return

    away_code   = game_data.get("away_code", "default")
    home_code   = game_data.get("home_code", "default")
    away_score  = game_data.get("away_score", 0)
    home_score  = game_data.get("home_score", 0)
    away_record = game_data.get("away_record", "0-0")
    home_record = game_data.get("home_record", "0-0")

    # Fill away background
    away_bg = teams_conf["background"]["away"]
    away_bg_col = get_team_background_color(away_code)
    fill_rect(canvas, away_bg["x"], away_bg["y"], away_bg["width"], away_bg["height"], away_bg_col)

    # Away text
    away_name_conf = teams_conf["name"]["away"]
    away_text_col = get_team_text_color(away_code)
    away_disp = f"{away_code.upper()} ({away_record})"
    graphics.DrawText(canvas, font, away_name_conf["x"], away_name_conf["y"], away_text_col, away_disp)

    # Fill home background
    home_bg = teams_conf["background"]["home"]
    home_bg_col = get_team_background_color(home_code)
    fill_rect(canvas, home_bg["x"], home_bg["y"], home_bg["width"], home_bg["height"], home_bg_col)

    # Home text
    home_name_conf = teams_conf["name"]["home"]
    home_text_col  = get_team_text_color(home_code)
    home_disp      = f"{home_code.upper()} ({home_record})"
    graphics.DrawText(canvas, font, home_name_conf["x"], home_name_conf["y"], home_text_col, home_disp)

    # Score text color from scoreboard.json default
    away_runs_conf = teams_conf["runs"]["away"]
    home_runs_conf = teams_conf["runs"]["home"]
    sc_col = get_scoreboard_color("default", "text")

    graphics.DrawText(canvas, font,
                      away_runs_conf["x"], away_runs_conf["y"],
                      sc_col, str(away_score))

    graphics.DrawText(canvas, font,
                      home_runs_conf["x"], home_runs_conf["y"],
                      sc_col, str(home_score))

def draw_pregame(canvas, font, game_data):
    """
    Draw background + pitching matchup + start time in pre-game.
    We'll assume game_data includes:
      - away_pitcher
      - home_pitcher
      - start_time
    """
    bg_col = get_scoreboard_color("default", "background")
    fill_rect(canvas, 0, 0, 64, 32, bg_col)

    # Possibly get layout coords from scoreboard.json => "pregame" or just pick some defaults
    matchup_col = get_scoreboard_color("pregame", "matchup")
    start_col   = get_scoreboard_color("pregame", "start_time")

    away_pitcher = game_data.get("away_pitcher", "TBD")
    home_pitcher = game_data.get("home_pitcher", "TBD")
    start_time = convert_start_time_to_est(game_data.get("start_time", "TBD"))
    #start_time   = game_data.get("start_time", "TBD")
    
    print(game_data)
    
    # Show the matchup: e.g. "VERLANDER vs SALE"
    pitch_str = f"{away_pitcher} vs {home_pitcher}"
    graphics.DrawText(canvas, font, 2, 20, matchup_col, pitch_str)

    pregame_starttime = get_layout("pregame", "start_time")
    x = pregame_starttime["x"]
    y = pregame_starttime["y"]
    # Show the start time, e.g. "7:05 PM"
    graphics.DrawText(canvas, font, x, y, start_col, start_time)

def draw_final(canvas, font, game_data):
    bg_col = get_scoreboard_color("default", "background")
    fill_rect(canvas, 0, 0, 64, 32, bg_col)
    final_conf = get_layout("final", "inning")
    if final_conf:
        x = final_conf["x"]
        y = final_conf["y"]
        fin_col = get_scoreboard_color("final", "inning")
        graphics.DrawText(canvas, font, x, y, fin_col, "FINAL")

def draw_offday(canvas, font):
    bg_col = get_scoreboard_color("default", "background")
    fill_rect(canvas, 0, 0, 64, 32, bg_col)
    off_col = get_scoreboard_color("offday", "scrolling_text")
    graphics.DrawText(canvas, font, 1, 16, off_col, "Off Day")
