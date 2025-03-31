# main.py
import time
import datetime
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

from scoreboard_data import fetch_today_tigers_game, fetch_last_final_tigers_game
from scoreboard_layout import get_default_font
from scoreboard_colors import get_scoreboard_color
from scoreboard_draw import (
    fill_rect, draw_count, draw_pregame, draw_offday, draw_final,
    draw_teams_and_score, draw_bases, draw_outs, draw_inning_arrow
)

def main():
    # 1) Configure the LED Matrix
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    # If Adafruit HAT, set this:
    options.hardware_mapping = "adafruit-hat"
    options.gpio_slowdown = 3
    options.disable_hardware_pulsing = True
    options.brightness = 75

    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()

    # 2) Load default font from w64h32.json
    font_name = get_default_font()  # e.g. "4x6"
    font_path = f"/home/pi/rpi-rgb-led-matrix/fonts/{font_name}.bdf"
    fnt = graphics.Font()
    fnt.LoadFont(font_path)

    while True:
        # 3) Attempt to fetch today's Tigers game
        game_data = fetch_today_tigers_game()
        if not game_data:
            # No game => last final or offday
            final_data = fetch_last_final_tigers_game()
            canvas.Clear()
            if not final_data:
                # show offday
                draw_offday(canvas, fnt)
            else:
                # show final scoreboard
                draw_final(canvas, fnt, final_data)
                draw_teams_and_score(canvas, fnt, final_data)
            matrix.SwapOnVSync(canvas)
            time.sleep(60)
            continue

        # Check status from the game_data
        status = game_data["status"].lower()  # e.g. "scheduled", "pre-game", "in progress", "final"

        # 4) In-Progress
        if "progress" in status:
            while True:
                updated = fetch_today_tigers_game()
                if not updated:
                    # Maybe the game ended
                    break
                new_stat = updated["status"].lower()
                if "final" in new_stat or "game over" in new_stat:
                    # Switched to final
                    canvas.Clear()
                    draw_final(canvas, fnt, updated)
                    draw_teams_and_score(canvas, fnt, updated)
                    matrix.SwapOnVSync(canvas)
                    time.sleep(60)
                    break

                canvas.Clear()
                # fill background
                bg_col = get_scoreboard_color("default", "background")
                fill_rect(canvas, 0, 0, 64, 32, bg_col)

                draw_teams_and_score(canvas, fnt, updated)
                draw_bases(canvas, updated)
                draw_outs(canvas, updated)
                draw_inning_arrow(canvas, fnt, updated)
                draw_count(canvas, fnt, updated)

                matrix.SwapOnVSync(canvas)
                time.sleep(15)

        # 5) If direct final
        elif "final" in status:
            canvas.Clear()
            draw_final(canvas, fnt, game_data)
            draw_teams_and_score(canvas, fnt, game_data)
            matrix.SwapOnVSync(canvas)
            time.sleep(60)

        # 6) Pre-game or scheduled
        else:
            # "Scheduled", "Pre-Game", "Warmup"
            while True:
                updated = fetch_today_tigers_game()
                if not updated:
                    break
                new_stat = updated["status"].lower()
                if "progress" in new_stat:
                    # Switch to in-progress
                    break
                if "final" in new_stat or "game over" in new_stat:
                    # Possibly the game ended
                    canvas.Clear()
                    draw_final(canvas, fnt, updated)
                    draw_teams_and_score(canvas, fnt, updated)
                    matrix.SwapOnVSync(canvas)
                    time.sleep(60)
                    break

                canvas.Clear()
                draw_pregame(canvas, fnt, updated)      # shows pitcher matchup, start time
                draw_teams_and_score(canvas, fnt, updated)  
                matrix.SwapOnVSync(canvas)
                time.sleep(30)

if __name__ == "__main__":
    from scoreboard_draw import fill_rect
    main()
