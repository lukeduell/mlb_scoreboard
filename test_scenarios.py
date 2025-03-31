#!/usr/bin/env python3

import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# We'll import from our existing modules:
from scoreboard_layout import get_layout, get_default_font
from scoreboard_colors import get_scoreboard_color
from scoreboard_draw import (
    fill_rect, draw_pregame, draw_teams_and_score,
    draw_bases, draw_outs, draw_inning_arrow, draw_count, draw_final
)

def main():
    # 1) Configure the LED Matrix
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.brightness = 50
    # If you're using an Adafruit HAT or different hardware, set accordingly:
    options.hardware_mapping = "adafruit-hat"
    # If you want real-time color rendering, remove or set capabilities, but let's keep it simple:
    options.disable_hardware_pulsing = True
    # Adjust slowdown if you get flicker
    options.gpio_slowdown = 4

    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()

    # 2) Load a default font from w64h32.json or just pick "4x6"
    font_name = get_default_font()  # e.g. "4x6"
    font_path = f"/home/pi/rpi-rgb-led-matrix/fonts/{font_name}.bdf"
    # Or if your fonts are in a different folder, point there:
    # font_path = "/home/pi/rpi-rgb-led-matrix/fonts/4x6.bdf"

    print(f"Using font: {font_path}")
    fnt = graphics.Font()
    fnt.LoadFont(font_path)

    # -----------------------------------------------
    # 3) Mock a PRE-GAME scenario
    # -----------------------------------------------
    pregame_data = {
        "status": "Pre-Game",
        "home_code": "bos",
        "away_code": "det",
        "home_score": 0,
        "away_score": 0,
        "away_record": "11-0",
        "home_record": "9-2",
        "away_pitcher": "Verla",
        "home_pitcher": "Sale",
        "start_time": "7:05 PM",
        # If you want to test at-bat details or advanced stuff, not relevant for pregame
    }

    # Clear the canvas
    canvas.Clear()

    # Possibly fill the background with a default color
    bg_col = get_scoreboard_color("default","background")
    fill_rect(canvas, 0, 0, 64, 32, bg_col)

    # 3a) Draw the pre-game scoreboard layout
    draw_pregame(canvas, fnt, pregame_data)
    # 3b) Draw team bars, names, and scores
    draw_teams_and_score(canvas, fnt, pregame_data)

    matrix.SwapOnVSync(canvas)
    print("Showing PRE-GAME scenario for 5 seconds...")
    time.sleep(5)

    # -----------------------------------------------
    # 4) Mock an IN-GAME scenario
    # -----------------------------------------------
    in_progress_data = {
        "status": "In Progress",
        "home_code": "mil",
        "away_code": "det",
        "home_score": 3,
        "away_score": 2,
        "inning": 5,
        "is_top_inning": True,
        "outs": 1,
        "runners_on": ["1B","2B"]  # sample runners
    }

    canvas.Clear()
    # fill background
    bg_col = get_scoreboard_color("default","background")
    fill_rect(canvas, 0, 0, 64, 32, bg_col)

    # 4a) Teams & score
    draw_teams_and_score(canvas, fnt, in_progress_data)
    # 4b) Bases
    draw_bases(canvas, in_progress_data)
    # 4c) Outs
    draw_outs(canvas, in_progress_data)
    # 4d) Inning arrow
    draw_inning_arrow(canvas, fnt, in_progress_data)
    draw_count(canvas, fnt, in_progress_data)

    matrix.SwapOnVSync(canvas)
    print("Showing IN-GAME scenario for 5 seconds...")
    time.sleep(5)
    
    # -----------------------------------------------
    # 4) Mock an FINAL scenario
    # -----------------------------------------------
    
    final_data = {
        "status": "Final",
        "home_code": "bos",
        "away_code": "det",
        "home_score": 5,
        "away_score": 0,
        "inning": 9,
        "is_top_inning": False,
        "outs": 3,
        
        # If you want to test at-bat details or advanced stuff, not relevant for pregame
    }

    # Clear the canvas
    canvas.Clear()

    # Possibly fill the background with a default color
    bg_col = get_scoreboard_color("default","background")
    fill_rect(canvas, 0, 0, 64, 32, bg_col)

    # 3a) Draw the pre-game scoreboard layout
    draw_final(canvas, fnt, final_data)
    # 3b) Draw team bars, names, and scores
    draw_teams_and_score(canvas, fnt, final_data)

    matrix.SwapOnVSync(canvas)
    print("Showing PRE-GAME scenario for 5 seconds...")
    time.sleep(15)

    # Done - clear and exit
    canvas.Clear()
    matrix.SwapOnVSync(canvas)
    print("Test complete.")

if __name__ == "__main__":
    main()
