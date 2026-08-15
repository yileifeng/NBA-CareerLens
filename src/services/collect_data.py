import re
import pandas as pd

from nba_api.stats.endpoints import leaguedashplayerstats
from src.database import db
from src.models import Player, PlayerSeason
from src.messaging.publisher import publish_season_collected

SEASON_PATTERN = re.compile(r"(\d{4})-(\d{2})")
REQ_COLS = {
    "PLAYER_ID",
    "PLAYER_NAME",
    "TEAM_ID",
    "TEAM_ABBREVIATION",
    "AGE",
    "GP",
    "MIN",
    "PTS",
    "REB",
    "AST",
    "STL",
    "BLK",
    "TOV",
    "FG_PCT",
    "FG3_PCT",
    "FT_PCT",
    "PLUS_MINUS"
}

# clean DB row values
def clean_val(row: dict, col: str, type: type[int] | type[float] | type[str]):
    val = row.get(col)
    if val is None or pd.isna(val):
        return None
    
    # cast to the appropriate type
    return type(val)

# collect player stats for season
def collect_player_stats(season: str):
    # make NBA API call to get player stats
    response = leaguedashplayerstats.LeagueDashPlayerStats(season=season, season_type_all_star='Regular Season', per_mode_detailed='PerGame', timeout=60)
    
    df = response.league_dash_player_stats.get_data_frame()
    # error check for failed request
    if df.empty:
        print(f"No data found for season {season}")
        return
    
    missing_cols = REQ_COLS - set(df.columns)
    # error check for missing required cols
    if missing_cols:
        missing = ', '.join(missing_cols)
        print(f"Missing columns in API response for season {season}: {missing}")
    
    return df.to_dict(orient='records')

# insert / update player stats in DB
def import_db_player_stats(season: str):
    rows = collect_player_stats(season)
    inserted = 0
    updated = 0
    
    try: 
        for row in rows:
            # fetch player from DB if exists
            player_id = int(row["PLAYER_ID"])
            player_name = str(row["PLAYER_NAME"])
            player = db.session.get(Player, player_id)
            
            if player is None:
                # create new player profile and add to DB
                player = Player(player_id=player_id, player_name=player_name)
                db.session.add(player)
            else:
                player.player_name = player_name
            
            # fetch player season stats from DB if exists
            query = db.select(PlayerSeason).filter_by(player_id=player_id, season=season)
            player_season = db.session.execute(query).scalar_one_or_none()
            
            # updated player season stats values
            values = {
                "team_id": clean_val(row, "TEAM_ID", int),
                "team_abbreviation": clean_val(row, "TEAM_ABBREVIATION", str),
                "age": clean_val(row, "AGE", int),
                "games_played": clean_val(row, "GP", int),
                "minutes_per_game": clean_val(row, "MIN", float),
                "points_per_game": clean_val(row, "PTS", float),
                "rebounds_per_game": clean_val(row, "REB", float),
                "assists_per_game": clean_val(row, "AST", float),
                "steals_per_game": clean_val(row, "STL", float),
                "blocks_per_game": clean_val(row, "BLK", float),
                "turnovers_per_game": clean_val(row, "TOV", float),
                "field_goal_pct": clean_val(row, "FG_PCT", float),
                "three_point_pct": clean_val(row, "FG3_PCT", float),
                "free_throw_pct": clean_val(row, "FT_PCT", float),
                "plus_minus": clean_val(row, "PLUS_MINUS", float),
            }
            
            if player_season is None:
                # create new player season record and add to DB
                player_season = PlayerSeason(player_id=player_id, season=season, **values)
                db.session.add(player_season)
                inserted += 1
            else:
                # otherwise update existing player season record with new values
                for attr, val in values.items():
                    setattr(player_season, attr, val)
                updated += 1

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    
    res = {
        "season": season,
        "received": len(rows),
        "inserted": inserted,
        "updated": updated
    }
    
    # publish to message queue after DB commit
    publish_season_collected(season=season, players=len(rows), inserted=inserted, updated=updated)
    
    return res

            