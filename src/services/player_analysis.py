import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from src.database import db
from src.models import PlayerSeason

# features for data analysis
ANALYSIS_STATS = [
    "minutes_per_game",
    "points_per_game",
    "rebounds_per_game",
    "assists_per_game",
    "steals_per_game",
    "blocks_per_game",
    "turnovers_per_game",
    "field_goal_pct",
    "three_point_pct",
    "free_throw_pct",
    "plus_minus",
]

# obtain player season data from DB in Pandas DF format
def get_season_data(season: str):
    # SQL query to extract player seasons data
    query = (db.select(PlayerSeason).where(PlayerSeason.season == season))
    player_seasons = db.session.execute(query).scalars().all()
    # print('player seasons: ', player_seasons)
    
    res = []
    # extract each row from data
    for season in player_seasons:
        res.append({
            "player_id": season.player_id,
            "player_name": season.player.player_name,
            "season": season.season,
            "age": season.age,
            "games_played": season.games_played,
            "minutes_per_game": season.minutes_per_game,
            "points_per_game": season.points_per_game,
            "rebounds_per_game": season.rebounds_per_game,
            "assists_per_game": season.assists_per_game,
            "steals_per_game": season.steals_per_game,
            "blocks_per_game": season.blocks_per_game,
            "turnovers_per_game": season.turnovers_per_game,
            "field_goal_pct": season.field_goal_pct,
            "three_point_pct": season.three_point_pct,
            "free_throw_pct": season.free_throw_pct,
            "plus_minus": season.plus_minus,
        })
    
    # convert to Pandas df
    return pd.DataFrame(res)

# basic data cleaning
def clean_data(season: str):
    df = get_season_data(season)
    # print(df, season)
    if df.empty:
        return

    # filter out low sample size outliers
    df = df[(df["games_played"] >= 10) & (df["minutes_per_game"] >= 10)].copy()
    
    # remove NA values
    df = df.dropna(subset=ANALYSIS_STATS)
    
    print(f'Total values: {len(df)}')
    return df

# add new column for every stat to show player percentile in that statistic
def calc_percentiles(season: str):
    df = clean_data(season)
    for stat in ANALYSIS_STATS:
        # compute percentile relative to rest of col
        percentile_val = df[stat].rank(pct=True) * 100
        if stat == 'turnovers_per_game':
            # turnovers should be reversed (less is better)
            df[f"{stat}_percentile"] = df[stat].rank(pct=True, ascending=False) * 100
        else:
            df[f"{stat}_percentile"] = percentile_val
    
    return df

# look for players with similar statistical profiles
def find_similar_comparisons(player_id: int, season: str, limit: int = 5):
    df = clean_data(season)
    # base case error check
    if player_id not in df["player_id"].values:
        return
    
    # scale each player statistic to be more meaningful when computing distance
    scaler = StandardScaler()
    std_stats = scaler.fit_transform(df[ANALYSIS_STATS])
    
    # find df index for selected player and convert to row position 
    player_idx = df.index[df["player_id"] == player_id][0]
    pos = df.index.get_loc(player_idx)
    
    # compute player similarity scores using cosine similarity
    sim_scores = cosine_similarity(std_stats[pos].reshape(1, -1), std_stats)[0]
    
    # construct output with playerid, player name, relevant stats for reference purposes and cosine sim score
    sim_players = df[["player_id", "player_name", "points_per_game", "rebounds_per_game", "assists_per_game"]].copy()
    sim_players["similarity"] = sim_scores
    # remove selected player
    sim_players = sim_players[sim_players["player_id"] != player_id]
    
    # get top limit comparable players
    sim_players = sim_players.sort_values("similarity", ascending=False).head(limit)
    
    # format the output into more user readable format
    res = []
    for _, row in sim_players.iterrows():
        res.append({
            "player_id": int(row["player_id"]),
            "player_name": row["player_name"],
            "similarity": float(row["similarity"]),
            "stats": {
                "points_per_game": float(row["points_per_game"]),
                "rebounds_per_game": float(row["rebounds_per_game"]),
                "assists_per_game": float(row["assists_per_game"])
            }
        })

    return res
