import os
import click
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from prometheus_client import Counter

from src.database import db, migrate
from src.models import Player, PlayerSeason
from src.services.collect_data import import_db_player_stats
from src.services.player_analysis import calc_percentiles, find_similar_comparisons
from src.services.season_utils import generate_seasons
from src.services.data_summary import get_summary
from src.services.trajectory_analysis import build_df, find_similar_trajectories
from src.services.player_projection import project_player_stats

load_dotenv()

req_count = Counter(
    "http_requests_total",
    "Total number of app requests received"
)
request_count = 0

start_time = time.time()

# normalize database URL for SQLAlchemy
def normalize_db_url(db_url: str) -> str:
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql://", 1)
    return db_url

# setup Flask app and DB
def create_app():
    app = Flask(__name__)
    db_url = os.getenv("DATABASE_URL", "sqlite:///data.db")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = normalize_db_url(db_url)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # base route
    @app.get("/")
    def home():
        return render_template("index.html")

    # route to import player stats for a given season    
    @app.get("/api/player-seasons")
    def get_player_seasons():
        season = request.args.get("season")
        search = request.args.get("search", "").strip()

        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=25, type=int)
        
        # join PlayerSeason to Player for search and sorting
        query = db.select(PlayerSeason).join(Player)
        # apply season filters
        if season:
            query = query.where(PlayerSeason.season == season)
        # player search
        if search:
            query = query.where(Player.player_name.ilike(f"%{search}%"))
            
        # pagination
        query = query.order_by(Player.player_name, PlayerSeason.season.desc())
        pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "items": [
                {
                    "player_id": row.player_id,
                    "player_name": row.player.player_name,
                    "season": row.season,
                    "team_abbreviation": row.team_abbreviation,
                    "age": row.age,
                    "games_played": row.games_played,
                    "minutes_per_game": row.minutes_per_game,
                    "points_per_game": row.points_per_game,
                    "rebounds_per_game": row.rebounds_per_game,
                    "assists_per_game": row.assists_per_game,
                    "field_goal_pct": row.field_goal_pct,
                    "three_point_pct": row.three_point_pct,
                    "free_throw_pct": row.free_throw_pct,
                }
                for row in pagination.items
            ],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_items": pagination.total,
                "total_pages": pagination.pages,
                "has_previous": pagination.has_prev,
                "has_next": pagination.has_next,
                "previous_page": pagination.prev_num,
                "next_page": pagination.next_num,
            },
            "filters": {
                "season": season,
                "search": search,
            },
        }), 200
        
    # route to get all available seasons
    @app.get("/api/seasons")
    def get_available_seasons():
        seasons = db.session.execute(db.select(PlayerSeason.season).distinct().order_by(PlayerSeason.season.desc())).scalars().all()
        return jsonify({
            "seasons": seasons
        }), 200
        
    # route to get player details page
    @app.get("/players/<int:player_id>")
    def player_details(player_id: int):
        return render_template("player.html", player_id=player_id)
    
    # collect and store one NBA season
    @app.cli.command("collect-season")
    @click.option("--season", default="2025-26", help="NBA Season in format YYYY-YY")
    def collect_season_data(season: str):
        click.echo(f"Collecting player stats for season {season}...")
        try:
            res = import_db_player_stats(season)
        except Exception as error:
            click.echo(f"Error occurred while collecting player stats for season {season}: {error}")
            return
        
    # collect and store multiple NBA seasons
    @app.cli.command("collect-seasons")
    @click.option("--start-season", required=True, help="NBA starting season in format YYYY-YY")
    @click.option("--end-season", required=True, help="NBA ending season in format YYYY-YY")
    @click.option("--delay", default=2.0, show_default=True, type=float, help="Delay between requests")
    def collect_seasons_data(start_season: str, end_season: str, delay: float):
        seasons = generate_seasons(start_season=start_season, end_season=end_season)
        click.echo(f"Collecting player stats for {len(seasons)} seasons...")

        # collect data for each NBA season
        for season in seasons:
            try:
                res = import_db_player_stats(season)
                time.sleep(delay)
            except Exception as error:
                click.echo(f"Error occurred while collecting player stats for season {season}: {error}")
                return

    # route to get similar players to selected player in statistical profile        
    @app.get("/api/players/<int:player_id>/similar")
    def get_similar_players(player_id: int):
        # TODO: POC based only on 25-26 season
        season = request.args.get("season", "2025-26")
        limit = request.args.get("limit", default=5, type=int)
        
        try:
            res = find_similar_comparisons(player_id=player_id, season=season, limit=limit)
            return jsonify({
                "player_id": player_id,
                "season": season,
                "similar_players": res
            })
        except ValueError as error:
            return jsonify({
                "error": str(error)
            }), 404

    # route to calculate player percentiles in stats categories
    @app.get("/api/players/<int:player_id>/analysis")
    def get_player_analysis(player_id):
        # TODO: POC based only on 25-26 season
        season = request.args.get("season", "2025-26")
        res = calc_percentiles(season)
        player = res[res["player_id"] == player_id]
        row = player.iloc[0]
        
        # return JSON format of all player percentiles in each cato
        return jsonify({
            "player_id": int(row["player_id"]),
            "player_name": row["player_name"],
            "season": season,
            "stats": {
                "points_per_game": row["points_per_game"],
                "rebounds_per_game": row["rebounds_per_game"],
                "assists_per_game": row["assists_per_game"],
                "steals_per_game": row["steals_per_game"],
                "blocks_per_game": row["blocks_per_game"],
            },
            "percentiles": {
                "points": row["points_per_game_percentile"],
                "rebounds": row["rebounds_per_game_percentile"],
                "assists": row["assists_per_game_percentile"],
                "steals": row["steals_per_game_percentile"],
                "blocks": row["blocks_per_game_percentile"],
                "field_goal_pct": row["field_goal_pct_percentile"],
                "three_point_pct": row["three_point_pct_percentile"],
                "free_throw_pct": row["free_throw_pct_percentile"],
                "plus_minus": row["plus_minus_percentile"],
            }
        })
    
    # route to get app health
    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok"
        }), 200
        
    # increment request count before each request
    @app.before_request
    def count_request():
        global request_count
        req_count.inc()
        
        if request.path not in ["/health", "/metrics"]:
            request_count += 1
        
    # route to get app metrics
    @app.get("/metrics")
    def metrics():
        runtime = time.time() - start_time
        requests_per_second = request_count / runtime if runtime > 0 else 0
        return jsonify({
            "total_requests": request_count,
            "requests_per_second": requests_per_second,
            "uptime": runtime
        }), 200
        
    # get a summary of data collected
    @app.cli.command("collection-summary")
    def collection_summary():
        summary = get_summary()
        click.echo(f"Unique players: {summary['players']}")
        click.echo(f"Player season records: {summary['player_seasons']}")
        
        for season in summary["seasons"]:
            click.echo(f"- {season['season']}: {season['player_count']} players")
            
    # route to obtain players with similar trajectories to player id
    @app.get("/api/players/<int:player_id>/trajectory-comp")
    def get_trajectory_comps(player_id: int):
        num_seasons = request.args.get("seasons", default=3, type=int)
        limit = request.args.get("limit", default=5, type=int)
        
        try:
            # compute players with most limit similar trajectories
            trajectory_df = build_df()
            comps = find_similar_trajectories(player_id=player_id, df=trajectory_df, num_seasons=num_seasons, limit=limit)
            
            # find target player
            target_player = trajectory_df[trajectory_df["player_id"] == player_id]
            player_name = target_player.iloc[0]["player_name"]
            
            return jsonify({
                "player_id": player_id,
                "player_name": player_name,
                "seasons": num_seasons,
                "trajectory_comparisons": comps
            }), 200
            
        except ValueError as error:
            return jsonify({
                "error": str(error)
            }), 404
            
    # route to obtain projections for players for next season
    @app.get("/api/players/<int:player_id>/projection")
    def get_player_projections(player_id: int):
        history = request.args.get("history", default=3, type=int)
        try:
            # call method to predict player stats for next season
            trajectory_df = build_df()
            projection = project_player_stats(trajectory_df=trajectory_df, player_id=player_id, history=history)
            
            return jsonify(projection), 200

        except ValueError as error:
            return jsonify({
                "error": str(error)
            }), 404

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)