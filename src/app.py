import os
import click

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from src.database import db, migrate
from src.models import PlayerSeason
from src.services.collect_data import import_db_player_stats

load_dotenv()

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
        return """
        <h1>NBA CareerLens</h1>
        <p>The application is running.</p>
        """

    # route to import player stats for a given season    
    @app.get("/api/player-seasons")
    def get_player_seasons():
        # temporary only 2025-26
        season = request.args.get("season", "2025-26")
        # limit the number of results
        requested_limit = request.args.get("limit", default=25, type=int)
        limit = max(1, min(requested_limit, 100))
        
        query = (db.select(PlayerSeason).where(PlayerSeason.season == season).order_by(PlayerSeason.points_per_game.desc()).limit(limit))
        players = db.session.execute(query).scalars().all()
        
        return jsonify({
            "season": season,
            "count": len(players),
            "players": [player.to_dict() for player in players]
        })
    
    # collect and store one NBA season
    @app.cli.command("collect-season")
    @click.option("--season", default="2025-26", help="NBA Season in format YYYY-YY")
    def collect_season_data(season):
        click.echo(f"Collecting player stats for season {season}...")
        try:
            res = import_db_player_stats(season)
        except Exception as error:
            click.echo(f"Error occurred while collecting player stats for season {season}: {error}")
            return

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)