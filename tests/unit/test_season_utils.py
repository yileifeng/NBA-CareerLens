import pytest
from src.services.season_utils import generate_seasons, parse_season_starting_year

# test parse season starting year util method
def test_parse_season_starting_year():
    assert parse_season_starting_year("2025-26") == 2025

# test generate seasons util method    
def test_generate_seasons():
    seasons = generate_seasons(start_season="2021-22", end_season="2025-26")
    assert seasons == ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]