import re
# YYYY-YY (e.g. 2025-26)
season_regex = re.compile(r"^(\d{4})-(\d{2})$")

# return starting year from NBA season
def parse_season_starting_year(season: str) -> int:
    # might need error checking
    season = season_regex.fullmatch(season)
    if season is None:
        raise ValueError("Invalid season format")

    start_year = int(season.group(1))
    return start_year

# generate all NBA seasons between start and end season
def generate_seasons(start_season: str, end_season: str) -> list[str]:
    start_year = parse_season_starting_year(start_season)
    end_year = parse_season_starting_year(end_season)
    
    seasons = []
    # add every season in between
    for year in range(start_year, end_year + 1):
        next_year = (year + 1) % 100
        seasons.append(f"{year}-{next_year:02d}")
        
    return seasons
