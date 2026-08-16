from sqlalchemy import func
from src.database import db
from src.models import Player, PlayerSeason

# get a summary of data collection process
def get_summary() -> dict:
    player_count = db.session.scalar(db.select(func.count()).select_from(Player))
    player_season_count = db.session.scalar(db.select(func.count()).select_from(PlayerSeason))
    
    season_rows = db.session.execute(db.select(PlayerSeason.season, func.count(PlayerSeason.id)).group_by(PlayerSeason.season).order_by(PlayerSeason.season)).all()
    
    return {
        "players": player_count,
        "player_seasons": player_season_count,
        "seasons": [
            {
                "season": season,
                "player_count": count
            }
            for season, count in season_rows
        ]
    }