import pandas as pd
from src.services.player_projection import build_projection

# test projection builder method
def test_build_projection():
    df = pd.DataFrame([
        {
            "player_id": 1,
            "player_name": "Aaron Knight",
            "season": "2021-22",
            "years_of_experience": 1,
            "points_per_game": 19.0,
            "rebounds_per_game": 2.2,
            "assists_per_game": 5.4,
        },
        {
            "player_id": 1,
            "player_name": "Aaron Knight",
            "season": "2022-23",
            "years_of_experience": 2,
            "points_per_game": 22.1,
            "rebounds_per_game": 2.5,
            "assists_per_game": 6.7,
        },
        {
            "player_id": 1,
            "player_name": "Aaron Knight",
            "season": "2023-24",
            "years_of_experience": 3,
            "points_per_game": 25.6,
            "rebounds_per_game": 3.4,
            "assists_per_game": 7.2,
        },
        {
            "player_id": 1,
            "player_name": "Aaron Knight",
            "season": "2024-25",
            "years_of_experience": 4,
            "points_per_game": 25.2,
            "rebounds_per_game": 3.2,
            "assists_per_game": 7.5,
        }
    ])
    
    feats, projections, metadata = build_projection(df, history=3)
    
    assert(len(feats) == 1)
    assert(len(projections) == 1)
    assert(len(metadata) == 1)
    
    assert(feats.iloc[0]["year_1_points_per_game"] == 19.0)
    assert(feats.iloc[0]["year_3_assists_per_game"] == 7.2)
    assert(projections.iloc[0]["next_points_per_game"] == 25.2)
    assert(projections.iloc[0]["next_rebounds_per_game"] == 3.2)
    assert(projections.iloc[0]["next_assists_per_game"] == 7.5)
    
    assert(metadata.iloc[0]["projection_season"] == "2024-25")
