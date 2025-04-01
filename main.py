import time
from datetime import datetime
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

from data.game import Game
from data.update import UpdateStatus
from data.team import TEAM_ID_NAME
import debug

from scoreboard_layout import get_default_font
from scoreboard_colors import get_scoreboard_color
from scoreboard_draw import (
    fill_rect, draw_count, draw_pregame, draw_offday, draw_final,
    draw_teams_and_score, draw_bases, draw_outs, draw_inning_arrow
)

def fetch_today_tigers_game():
    # Replace this with logic to fetch today's Tigers game using the Game class
    tigers_id = 116  # Detroit Tigers team ID
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        games = Game.from_scheduled({"game_id": tigers_id, "game_date": today}, delay=10)
        return games
    except Exception as e:
        debug.error(f"Error fetching today's Tigers game: {e}")
        return None

def fetch_last_final_tigers_game():
    # Replace this with logic to fetch the last final Tigers game using the Game class
    return None  # Placeholder for now

def main():
    # 1) Configure the LED Matrix
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.hardware_mapping = "adafruit-hat"
    options.gpio_slowdown = 3
    options.disable_hardware_pulsing = True
    options.brightness = 75

    matrix = RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()

    # 2) Load default font
    font_name = get_default_font()
    font_path = f"/home/pi/rpi-rgb-led-matrix/fonts/{font_name}.bdf"
    fnt = graphics.Font()
    fnt.LoadFont(font_path)

    while True:
        # 3) Attempt to fetch today's Tigers game
        game = fetch_today_tigers_game()
        if not game:
            # No game => last final or offday
            final_data = fetch_last_final_tigers_game()
            canvas.Clear()
            if not final_data:
                draw_offday(canvas, fnt)
            else:
                draw_final(canvas, fnt, final_data)
                draw_teams_and_score(canvas, fnt, final_data)
            matrix.SwapOnVSync(canvas)
            time.sleep(60)
            continue

        # Check status from the game object
        status = game.status().lower()

        # 4) In-Progress
        if "progress" in status:
            while True:
                updated = fetch_today_tigers_game()
                if not updated:
                    break
                new_stat = updated.status().lower()
                if "final" in new_stat or "game over" in new_stat:
                    canvas.Clear()
                    draw_final(canvas, fnt, updated)
                    draw_teams_and_score(canvas, fnt, updated)
                    matrix.SwapOnVSync(canvas)
                    time.sleep(60)
                    break

                canvas.Clear()
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
            draw_final(canvas, fnt, game)
            draw_teams_and_score(canvas, fnt, game)
            matrix.SwapOnVSync(canvas)
            time.sleep(60)

        # 6) Pre-game or scheduled
        else:
            while True:
                updated = fetch_today_tigers_game()
                if not updated:
                    break
                new_stat = updated.status().lower()
                if "progress" in new_stat:
                    break
                if "final" in new_stat or "game over" in new_stat:
                    canvas.Clear()
                    draw_final(canvas, fnt, updated)
                    draw_teams_and_score(canvas, fnt, updated)
                    matrix.SwapOnVSync(canvas)
                    time.sleep(60)
                    break

                canvas.Clear()
                draw_pregame(canvas, fnt, updated)
                draw_teams_and_score(canvas, fnt, updated)
                matrix.SwapOnVSync(canvas)
                time.sleep(30)

if __name__ == "__main__":
    main()