# scoreboard_data.py

import requests
import datetime
import pytz
#from zoneinfo import ZoneInfo  # Available in Python 3.9+

API_BASE = "https://statsapi.mlb.com/api/v1"

def fetch_today_tigers_game():
    """
    Fetch today's MLB schedule, find if the Detroit Tigers are playing.
    Returns a dict that includes:
      status, home_code, away_code,
      home_score, away_score,
      inning, is_top_inning, outs, runners_on,
      away_pitcher, home_pitcher, away_record, home_record,
      start_time, ...
    or None if no Tigers game.
    """
    #today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    eastern = pytz.timezone("US/Eastern")
    now_est = datetime.datetime.now(eastern)
    today_str = now_est.strftime("%Y-%m-%d")
    print(today_str)
    
    url = f"{API_BASE}/schedule?sportId=1&date={today_str}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"[ERROR] Could not fetch schedule: {e}")
        return None

    if not data.get("dates"):
        return None

    games = data["dates"][0].get("games", [])
    for g in games:
        home_name = g["teams"]["home"]["team"]["name"]
        away_name = g["teams"]["away"]["team"]["name"]
        # Check if it's the Tigers
        if "Detroit Tigers" in (home_name, away_name):
            return build_game_data(g)
    return None

def fetch_last_final_tigers_game(days_back=14):
    """
    Look back up to `days_back` days for the most recent "Final" Tigers game.
    Returns a scoreboard dict in the same format as fetch_today_tigers_game,
    or None if not found.

    We do a day-by-day search going backwards from 'yesterday' to `days_back` days.
    As soon as we find a "Final" Tigers game, we parse it and return.
    """
    now = datetime.datetime.now()
    for offset in range(1, days_back+1):
        date_check = now - datetime.timedelta(days=offset)
        date_str = date_check.strftime("%Y-%m-%d")
        url = f"{API_BASE}/schedule?sportId=1&date={date_str}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"[ERROR] Could not fetch schedule for {date_str}: {e}")
            continue

        if not data.get("dates"):
            continue

        games = data["dates"][0].get("games", [])
        # Look for a Tigs final
        for g in games:
            home_name = g["teams"]["home"]["team"]["name"]
            away_name = g["teams"]["away"]["team"]["name"]
            status_str = g["status"]["detailedState"].lower()
            if "detroit tigers" in (home_name.lower(), away_name.lower()):
                # Check if final
                if "final" in status_str or "game over" in status_str:
                    # We found a final Tigers game
                    return build_game_data(g)
    return None

def build_game_data(g):
    """
    Given a single 'game' JSON from the schedule endpoint,
    build the scoreboard dict with extended data:
      - status
      - home/away code, score
      - inning, outs, runners
      - probable pitchers
      - records
      - start time
      if the game is in progress/final, we call fill_in_live_data for linescore.
    """
    home_name = g["teams"]["home"]["team"]["name"]
    away_name = g["teams"]["away"]["team"]["name"]
    game_data = {
        "status": g["status"]["detailedState"],   # e.g. "Scheduled", "Pre-Game", "In Progress", "Final"
        "home_team_name": home_name,
        "away_team_name": away_name,
        "home_score": g["teams"]["home"].get("score", 0),
        "away_score": g["teams"]["away"].get("score", 0),
        "is_top_inning": True,  # refine if linescore says so
        "inning": 0,
        "outs": 0,
        "runners_on": [],
        "away_pitcher": "TBD",
        "home_pitcher": "TBD",
        "away_record": "0-0",
        "home_record": "0-0",
        "start_time": "TBD",
    }

    # leagueRecord
    away_league_rec = g["teams"]["away"].get("leagueRecord", {})
    home_league_rec = g["teams"]["home"].get("leagueRecord", {})
    aw_wins = away_league_rec.get("wins", 0)
    aw_losses = away_league_rec.get("losses", 0)
    ho_wins = home_league_rec.get("wins", 0)
    ho_losses = home_league_rec.get("losses", 0)
    game_data["away_record"] = f"{aw_wins}-{aw_losses}"
    game_data["home_record"] = f"{ho_wins}-{ho_losses}"

    # probable pitchers
    away_pitcher_info = g["teams"]["away"].get("probablePitcher", {})
    home_pitcher_info = g["teams"]["home"].get("probablePitcher", {})
    if "fullName" in away_pitcher_info:
        game_data["away_pitcher"] = away_pitcher_info["fullName"]
    if "fullName" in home_pitcher_info:
        game_data["home_pitcher"] = home_pitcher_info["fullName"]

    # Start time from gameDate (UTC)
    game_date_str = g.get("gameDate", "")
    if game_date_str:
        try:
            dt_utc = datetime.datetime.fromisoformat(game_date_str.replace("Z",""))
            local_dt = dt_utc.astimezone()
            game_data["start_time"] = local_dt.strftime("%-I:%M %p")
        except ValueError:
            game_data["start_time"] = "TBD"

    # If in progress or final, fill linescore
    status_lc = game_data["status"].lower()
    if any(s in status_lc for s in ["in progress", "final", "game over", "completed early", "delayed", "manager challenge"]):
        fill_in_live_data(game_data, g["gamePk"])

    # Convert team names -> short code
    game_data["home_code"] = team_name_to_code(home_name)
    game_data["away_code"] = team_name_to_code(away_name)

    return game_data

def fill_in_live_data(game_data, game_pk):
    """
    If the game is in-progress/final, query the live feed for linescore data.
    """
    live_url = f"{API_BASE}.1/game/{game_pk}/feed/live"
    try:
        r = requests.get(live_url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        print(f"[ERROR] Could not fetch live feed: {e}")
        return

    linescore = data.get("liveData", {}).get("linescore", {})
    game_data["inning"] = linescore.get("currentInning", 0)
    game_data["is_top_inning"] = linescore.get("isTopInning", True)
    game_data["outs"] = linescore.get("outs", 0)

    # Runners
    offense = linescore.get("offense", {})
    runners_on = []
    if offense.get("first"):
        runners_on.append("1B")
    if offense.get("second"):
        runners_on.append("2B")
    if offense.get("third"):
        runners_on.append("3B")
    game_data["runners_on"] = runners_on

def team_name_to_code(full_name):
    """
    Convert full MLB team name to short code used in teams.json, e.g.:
      "Detroit Tigers" => "det", "Boston Red Sox" => "bos"
    """
    name_map = {
        "Arizona Diamondbacks": "az",
        "Atlanta Braves": "atl",
        "Baltimore Orioles": "bal",
        "Boston Red Sox": "bos",
        "Chicago Cubs": "chc",
        "Chicago White Sox": "cws",
        "Cincinnati Reds": "cin",
        "Cleveland Guardians": "cle",
        "Colorado Rockies": "col",
        "Detroit Tigers": "det",
        "Houston Astros": "hou",
        "Kansas City Royals": "kc",
        "Los Angeles Angels": "laa",
        "Los Angeles Dodgers": "lad",
        "Miami Marlins": "mia",
        "Milwaukee Brewers": "mil",
        "Minnesota Twins": "min",
        "New York Mets": "nym",
        "New York Yankees": "nyy",
        "Oakland Athletics": "ath",
        "Philadelphia Phillies": "phi",
        "Pittsburgh Pirates": "pit",
        "San Diego Padres": "sd",
        "San Francisco Giants": "sf",
        "Seattle Mariners": "sea",
        "St. Louis Cardinals": "stl",
        "Tampa Bay Rays": "tb",
        "Texas Rangers": "tex",
        "Toronto Blue Jays": "tor",
        "Washington Nationals": "wsh"
    }
    return name_map.get(full_name, "default")
