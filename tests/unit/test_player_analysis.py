import pandas as pd

from src.services import player_analysis

# test if percentiles rank stats properly
def test_calc_percentiles(monkeypatch):
    analysis_stats = ["points_per_game", "rebounds_per_game", "assists_per_game"]
    
    # mock data
    test_data = pd.DataFrame([
        {
            "player_id": 1,
            "player_name": "Bum",
            "points_per_game": 6.7,
            "rebounds_per_game": 4.2,
            "assists_per_game": 1.8,
        },
        {
            "player_id": 2,
            "player_name": "Mid",
            "points_per_game": 16.7,
            "rebounds_per_game": 3.5,
            "assists_per_game": 5.0,
        },
        {
            "player_id": 3,
            "player_name": "Star",
            "points_per_game": 26.7,
            "rebounds_per_game": 8.2,
            "assists_per_game": 8.6,
        }
    ])
    
    # replace analysis stats with smaller subset of stats for test
    monkeypatch.setattr(player_analysis, "ANALYSIS_STATS", analysis_stats)
    # drop the clean data step for test
    monkeypatch.setattr(player_analysis, "clean_data", lambda season: test_data.copy())
    
    res = player_analysis.calc_percentiles("2025-26")
    bum = res[res["player_id"] == 1].iloc[0]
    mid = res[res["player_id"] == 2].iloc[0]
    star = res[res["player_id"] == 3].iloc[0]
    
    assert (star["points_per_game_percentile"] > mid["points_per_game_percentile"] > bum["points_per_game_percentile"])
    
# test find similar player comparisons endpoint
def test_find_similar_comps(monkeypatch):
    analysis_stats = ["points_per_game", "rebounds_per_game", "assists_per_game"]
    
    test_data = pd.DataFrame([
        {
            "player_id": 1,
            "player_name": "All-around Player",
            "points_per_game": 20.0,
            "rebounds_per_game": 5.5,
            "assists_per_game": 5.6,
        },
        {
            "player_id": 2,
            "player_name": "Similar Player",
            "points_per_game": 21.8,
            "rebounds_per_game": 5.4,
            "assists_per_game": 5.2,
        },
        {
            "player_id": 3,
            "player_name": "Rebounding Specialist",
            "points_per_game": 6.2,
            "rebounds_per_game": 13.2,
            "assists_per_game": 1.0,
        },
        {
            "player_id": 4,
            "player_name": "High Volume Scorer",
            "points_per_game": 32.3,
            "rebounds_per_game": 2.1,
            "assists_per_game": 7.8,
        },
    ])
    
    # replace analysis stats with smaller subset of stats for test
    monkeypatch.setattr(player_analysis, "ANALYSIS_STATS", analysis_stats)
    # drop the clean data step for test
    monkeypatch.setattr(player_analysis, "clean_data", lambda season: test_data.copy())
    
    res = player_analysis.find_similar_comparisons(
        player_id=1,
        season="2025-26",
        limit=2,
    )
    
    assert len(res) == 2
    assert res[0]["player_id"] == 2
    assert res[0]["player_name"] == "Similar Player"
    
    assert "similarity" in res[0]
    assert "stats" in res[0]
