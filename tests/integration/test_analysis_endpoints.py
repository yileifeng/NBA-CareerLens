import pandas as pd
import src.app as app_module

# test find similar player comps endpoint
def test_similar_players_endpoint(client, monkeypatch):
    mock_comp = [
        {
            "player_id": 162067,
            "player_name": "Fake player",
            "similarity": 0.95,
            "stats": {
                "points_per_game": 28.2,
                "rebounds_per_game": 8.3,
                "assists_per_game": 8.5
            }
        }
    ]
    
    # change player ID as needed
    def mock_find_similar_comps(player_id, season, limit=5):
        assert player_id == 2544
        assert season == "2025-26"
        assert limit == 5
        
        return mock_comp
    
    monkeypatch.setattr(app_module, "find_similar_comparisons", mock_find_similar_comps)
    res = client.get("/api/players/2544/similar?season=2025-26")
    
    assert res.status_code == 200
    assert res.is_json
    
    body = res.get_json()
    
    assert body["player_id"] == 2544
    assert body["season"] == "2025-26"
    assert body["similar_players"] == mock_comp
    
# test calculate player stats percentiles endpoint
def test_player_analysis_endpoint(client, monkeypatch):
    # change as needed - LeBron
    mock_analysis = pd.DataFrame([
        {
            "player_id": 2544,
            "player_name": "LeBron James",
            "season": "2025-26",
            "points_per_game": 23.9,
            "rebounds_per_game": 6.1,
            "assists_per_game": 7.2,
            "steals_per_game": 1.2,
            "blocks_per_game": 0.6,
            "points_per_game_percentile": 90.5,
            "rebounds_per_game_percentile": 84.4,
            "assists_per_game_percentile": 97.4,
            "steals_per_game_percentile": 86.3,
            "blocks_per_game_percentile": 75.7,
            "field_goal_pct_percentile": 81.3,
            "three_point_pct_percentile": 26.9,
            "free_throw_pct_percentile": 33.1,
            "plus_minus_percentile": 76.4,
        },
    ])
    
    monkeypatch.setattr(app_module, "calc_percentiles", lambda season: mock_analysis.copy())
    # change player as needed - LeBron
    res = client.get("/api/players/2544/analysis?season=2025-26")
    
    assert res.status_code == 200
    assert res.is_json
    
    body = res.get_json()
    
    assert body["player_id"] == 2544
    assert body["player_name"] == "LeBron James"
    assert body["season"] == "2025-26"
    
    assert body["stats"]["points_per_game"] == 23.9
    assert body["percentiles"]["assists"] == 97.4
    assert body["percentiles"]["points"] == 90.5
    
# test find similar player trajectories endpoint
def test_trajectory_comps_endpoint(client, monkeypatch):
    mock_trajectory_df = pd.DataFrame([
        {
            "player_id": 1,
            "player_name": "Aaron Knight"
        }
    ])
    mock_comps = [
        {
            "player_id": 2,
            "player_name": "Sim player",
            "similarity": 0.95,
            "trajectory": [
                18.0, 2.2, 4.5,
                20.0, 2.5, 5.5,
                24.5, 3.1, 6.5
            ]
        }
    ]
    
    # override build trajectory dataframe
    monkeypatch.setattr(app_module, "build_df", lambda: mock_trajectory_df.copy())
    
    # mock find sim trajectories method
    def mock_find_sim_trajectories(player_id: int, df: pd.DataFrame, num_seasons: int, limit: int):
        assert player_id == 1
        assert num_seasons == 3
        assert limit == 5
        return mock_comps
    
    # override find similar trajectories method
    monkeypatch.setattr(app_module, "find_similar_trajectories", mock_find_sim_trajectories)
    
    res = client.get("/api/players/1/trajectory-comp?seasons=3&limit=5")
    
    assert res.status_code == 200
    body = res.get_json()
    assert body["player_id"] == 1
    assert body["player_name"] == "Aaron Knight"
    assert body["seasons"] == 3
    assert body["trajectory_comparisons"]== mock_comps
