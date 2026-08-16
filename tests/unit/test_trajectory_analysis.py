import pandas as pd
import pytest
from src.services.trajectory_analysis import add_experience_year, add_diff_changes, build_trajectory_vectors

# test years of experience method
def test_add_yoe_counts():
    df = pd.DataFrame([
        {
            "player_id": 1,
            "season": "2020-21"
        },
        {
            "player_id": 1,
            "season": "2021-22"
        },
        {
            "player_id": 2,
            "season": "2022-23"
        }
    ])
    
    res = add_experience_year(df)
    assert res[res["player_id"] == 1]["years_of_experience"].tolist() == [1, 2]
    assert res[res["player_id"] == 2]["years_of_experience"].tolist() == [1]
    
# test statistical changes year over year method
def test_diff_changes():
    df = pd.DataFrame([
        {
            "player_id": 1,
            "season": "2020-21",
            "points_per_game": 10.0
        },
        {
            "player_id": 1,
            "season": "2021-22",
            "points_per_game": 16.7
        }
    ])
    
    res = add_diff_changes(df, stats=["points_per_game"])
    first_year = res.iloc[0]
    second_year = res.iloc[1]
    
    assert pd.isna(first_year["points_per_game_change"])
    assert second_year["points_per_game_change"] == pytest.approx(6.7)
    
# test trajectory vectors builder
def test_build_trajectory_vectors():
    df = pd.DataFrame([
        {
            "player_id": 1,
            "player_name": "Aaron Knight",
            "years_of_experience": 1,
            "points_per_game": 19.0,
            "rebounds_per_game": 2.2,
            "assists_per_game": 5.4,
        },
        {
            "player_id": 1,
            "player_name": "Aaron Knight",
            "years_of_experience": 2,
            "points_per_game": 22.1,
            "rebounds_per_game": 2.5,
            "assists_per_game": 6.7,
        },
        {
            "player_id": 1,
            "player_name": "Aaron Knight",
            "years_of_experience": 3,
            "points_per_game": 25.6,
            "rebounds_per_game": 3.4,
            "assists_per_game": 7.2,
        }
    ])
    
    res = build_trajectory_vectors(df, num_seasons=3, stats=["points_per_game", "rebounds_per_game", "assists_per_game"])
    assert len(res) == 1
    assert res.iloc[0]["trajectory"] == [
        19.0, 2.2, 5.4,
        22.1, 2.5, 6.7,
        25.6, 3.4, 7.2
    ]
    