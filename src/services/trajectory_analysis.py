import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from src.database import db
from src.models import PlayerSeason

projection_stats = [
    "points_per_game",
    "rebounds_per_game",
    "assists_per_game"
]

# find all season data for a player from DB
def get_historical_seasons() -> pd.DataFrame:
    query = db.select(PlayerSeason).order_by(PlayerSeason.player_id, PlayerSeason.season)
    player_seasons = db.session.execute(query).scalars().all()
    
    res = []
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
            "free_throw_pct": season.free_throw_pct
        })
        
    return pd.DataFrame(res)

# add years of experience for player
def add_experience_year(df: pd.DataFrame) -> pd.DataFrame:
    res = df.sort_values(["player_id", "season"]).copy()
    res["years_of_experience"] = res.groupby("player_id").cumcount() + 1
    return res  

# add year-to-year statistical changes
def add_diff_changes(df: pd.DataFrame, stats: list[str] | None = None) -> pd.DataFrame:
    res = df.copy()
    player_stats = stats or projection_stats
    for stat in player_stats:
        # track previous stat
        res[f"prev_{stat}"] = res.groupby("player_id")[stat].shift(1)
        res[f"{stat}_change"] = res[stat] - res[f"prev_{stat}"]
    return res

# consolidates all functions
def build_df() -> pd.DataFrame:
    res = get_historical_seasons()
    res = add_experience_year(res)
    res = add_diff_changes(res)
    return res

# flatten a multi-season vector per player for players with at least num_seasons amount of data
def build_trajectory_vectors(df: pd.DataFrame, num_seasons: int = 3, stats: list[str] | None = None) -> pd.DataFrame:
    stats = stats or projection_stats
    # use only the first num_seasons
    selected_data = df[df["years_of_experience"] <= num_seasons].copy()
    selected_data = selected_data.dropna(subset=stats)
    
    # number of useful seasons - only use those players that meet num_seasons criteria
    season_counts = selected_data.groupby("player_id")["years_of_experience"].nunique()
    eligible_players = season_counts[season_counts == num_seasons].index
    selected_data = selected_data[selected_data["player_id"].isin(eligible_players)].sort_values(["player_id", "years_of_experience"])

    res = []
    # build up player vector over seasons
    for player_id, player_rows in selected_data.groupby("player_id"):
        player_rows = player_rows.sort_values("years_of_experience")
        vector = []
        # for each player season add PPG, RPG, APG
        for _, row in player_rows.iterrows():
            for stat in stats:
                vector.append(row[stat])
        res.append({
            "player_id": int(player_id),
            "player_name": player_rows.iloc[0]["player_name"],
            "trajectory": vector
        })
        
    return pd.DataFrame(res)

# discover similar player trajectories over multi-seasons
def find_similar_trajectories(player_id: int, df: pd.DataFrame, num_seasons: int = 3, limit: int = 5, stats: list[str] | None = None) -> list[dict]:
    vectors_df = build_trajectory_vectors(df=df, num_seasons=num_seasons, stats=stats)
    trajectory_stats = vectors_df["trajectory"].tolist()
    
    # standardize stats
    scaler = StandardScaler()
    std_trajectories = scaler.fit_transform(trajectory_stats)
    
    # find player
    player_idx = vectors_df.index[vectors_df["player_id"] == player_id][0]
    position = vectors_df.index.get_loc(player_idx)
    # find similarity scores to other trajectories
    sim_scores = cosine_similarity(std_trajectories[position].reshape(1, -1), std_trajectories)[0]
    
    sim_df = vectors_df[["player_id", "player_name", "trajectory"]].copy()
    sim_df["similarity"] = sim_scores
    # remove self
    sim_df = sim_df[sim_df["player_id"] != player_id]
    # sort similarity scores and obtain top 5
    sim_df = sim_df.sort_values("similarity", ascending=False).head(limit)
    
    res = []
    # structure similarity results output object
    for _, row in sim_df.iterrows():
        res.append({
            "player_id": int(row["player_id"]),
            "player_name": row["player_name"],
            "similarity": float(row["similarity"]),
            "trajectory": [val for val in row["trajectory"]]
        })

    return res
