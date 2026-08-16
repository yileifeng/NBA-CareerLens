import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

proj_stats = [
    "points_per_game",
    "rebounds_per_game",
    "assists_per_game"
]

# build basic projection model for predicting a player's next season stats
def build_projection(trajectory_df: pd.DataFrame, history: int = 3, stats: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    stats = stats or proj_stats
    # drop NA rows 
    data = trajectory_df.dropna(subset=stats).copy()
    data = data.sort_values(["player_id", "years_of_experience"])
    
    feat_rows = []
    target_rows = []
    metadata_rows = []
    # collect training examples for each player
    for player_id, player_rows in data.groupby("player_id"):
        # sort by years of experience
        player_rows = player_rows.sort_values("years_of_experience").reset_index(drop=True)
        # require at least history seasons + projection season]
        if len(player_rows) < history + 1:
            continue
        
        # sliding window across player's career (e.g. given seasons 1-3 predict season 4)
        for start_idx in range(len(player_rows) - history):
            # TODO: might need to fix for the case of a player missing a season
            # prev history # of seasons
            subset = player_rows.iloc[start_idx:start_idx + history]
            projection = player_rows.iloc[start_idx + history]
            
            # features track historical data
            feats = {}
            for year_num, (_, season_row) in enumerate(subset.iterrows(), start=1):
                for stat in stats:
                    feats[f"year_{year_num}_{stat}"] = float(season_row[stat])
            # projected year stats
            projections = { f"next_{stat}": float(projection[stat]) for stat in stats }
            
            feat_rows.append(feats)
            target_rows.append(projections)
            metadata_rows.append({
                "player_id": int(player_id),
                "player_name": player_rows.iloc[0]["player_name"],
                "projection_season": projection["season"],
                "projection_yoe": int(projection["years_of_experience"])
            })
    
    return (pd.DataFrame(feat_rows), pd.DataFrame(target_rows), pd.DataFrame(metadata_rows))

# split projection season into training and test
def split_projection(feats: pd.DataFrame, projections: pd.DataFrame, metadata: pd.DataFrame, test_season: str):
    # mark all seasons before test season as training
    train_seasons = metadata["projection_season"] < test_season
    test_seasons = metadata["projection_season"] == test_season
    
    # split inputs into train + test data
    feats_train, feats_test = feats.loc[train_seasons].reset_index(drop=True), feats.loc[test_seasons].reset_index(drop=True)
    projs_train, projs_test = projections.loc[train_seasons].reset_index(drop=True), projections.loc[test_seasons].reset_index(drop=True)
    metadata_train, metadata_test = metadata.loc[train_seasons].reset_index(drop=True), metadata.loc[test_seasons].reset_index(drop=True)
    
    return feats_train, feats_test, projs_train, projs_test, metadata_train, metadata_test

# train a random forest regressor to project next season statistics 
# TODO: can improve upon model complexity, type, etc
def train_projection_model(feats_train, projs_train) -> RandomForestRegressor:
    model = RandomForestRegressor(n_estimators=200, random_state=42, min_samples_leaf=3)
    model.fit(feats_train, projs_train)
    return model

# evaluate prediction model using MAE
def evaluate_model(model: RandomForestRegressor, feats_test: pd.DataFrame, projs_test: pd.DataFrame) -> dict:
    preds = model.predict(feats_test)
    preds_df = pd.DataFrame(preds, columns=projs_test.columns)
    
    metrics = {}
    for col in projs_test.columns:
        stat = col.removeprefix("next_")
        metrics[stat] = {
            # compute MAE using sklearn library with actual test data vs model preds
            "mean_absolute_error": float(mean_absolute_error(projs_test[col], preds_df[col]))
        }
    
    return metrics

# evaluate using baseline model that uses the same stats as the most recent season
def evaluate_baseline_model(feats_test: pd.DataFrame, projs_test: pd.DataFrame, history: int = 3, stats: list[str] | None = None) -> dict:
    stats = stats or proj_stats
    metrics = {}
    # for each stat measure MAE based on most recent season
    for stat in stats:
        feat_col = f"year_{history}_{stat}"
        proj_col = f"next_{stat}"
        metrics[stat] = {
            "mean_absolute_error": float(mean_absolute_error(projs_test[proj_col], feats_test[feat_col]))
        }
    
    return metrics

# summary method to build model and evaluate botht he random forest and baseline models
def build_projections(trajectory_df: pd.DataFrame, test_season: str = "2024-25", history: int = 3) -> dict:
    # build and split data
    feats, projs, metadata = build_projection(trajectory_df=trajectory_df, history=history)
    feats_train, feats_test, projs_train, projs_test, metadata_train, metadata_test = split_projection(feats=feats, projections=projs, metadata=metadata, test_season=test_season)
    
    # train model
    rf_model = train_projection_model(feats_train=feats_train, projs_train=projs_train)
    
    # evaluate models
    rf_model_metrics = evaluate_model(model=rf_model, feats_test=feats_test, projs_test=projs_test)
    baseline_model_metrics = evaluate_baseline_model(feats_test=feats_test, projs_test=projs_test)
    
    return {
        "model": rf_model,
        "model_metrics": rf_model_metrics,
        "baseline_model_metrics": baseline_model_metrics,
        "training_samples": len(feats_train),
        "test_samples": len(feats_test),
        "test_season": test_season,
        "test_metadata": metadata_test
    } 
