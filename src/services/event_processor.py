from src.services.player_analysis import calc_percentiles

# conduct season analysis after season data has been collected / updated
def process_season_collected(event: dict) -> dict:
    # compute percentile data for player stats
    data = event.get("data")
    season = data.get("season")
    percentiles = calc_percentiles(season)
    
    res = {
        "season": season,
        "players": len(percentiles)
    }
    
    return res