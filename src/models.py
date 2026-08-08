from datetime import datetime, timezone
from src.database import db

# obtain current UTC timezone time
def current_time():
    return datetime.now(timezone.utc)

# class model representing NBA player stored in DB
class Player(db.Model):
    __tablename__ = 'players'
    
    player_id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(120), nullable=False)
    
    # timestamp columns for created and updated time
    created_time = db.Column(db.DateTime(timezone=True), nullable=False, default=current_time)
    updated_time = db.Column(db.DateTime(timezone=True), nullable=False, default=current_time, onupdate=current_time)
    
    # setup DB relationship to PlayerSeason model
    seasons = db.relationship('PlayerSeason', back_populates='player')

# class model representing NBA player season stored in DB
class PlayerSeason(db.Model):
    __tablename__ = 'player_seasons'
    
    # setup DB columns
    id =  db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=False)
    
    season = db.Column(db.String(7), nullable=False)
    
    team_id = db.Column(db.BigInteger)
    team_abbreviation = db.Column(db.String(10))
    
    age = db.Column(db.Integer)
    games_played = db.Column(db.Integer)
    
    # player statistics 
    minutes_per_game = db.Column(db.Float)
    points_per_game = db.Column(db.Float)
    rebounds_per_game = db.Column(db.Float)
    assists_per_game = db.Column(db.Float)
    steals_per_game = db.Column(db.Float)
    blocks_per_game = db.Column(db.Float)
    turnovers_per_game = db.Column(db.Float)
    
    field_goal_pct = db.Column(db.Float)
    three_point_pct = db.Column(db.Float)
    free_throw_pct = db.Column(db.Float)
    plus_minus = db.Column(db.Float)
    
    collected_time = db.Column(db.DateTime(timezone=True), nullable=False, default=current_time)
    
    # setup DB relationship to Player model
    player = db.relationship('Player', back_populates='seasons', lazy='joined')
    
    # setup unique constraint to ensure that each player can only have one entry per season and season type
    __table_args__ = (
        db.UniqueConstraint('player_id', 'season', name='unique_player_season'),
    )
    
    # convert Player Season model to dictionary
    def to_dict(self):
        return {
            'player_id': self.player_id,
            'name': self.player.player_name,
            'season': self.season,
            'team': self.team_abbreviation,
            'age': self.age,
            'games_played': self.games_played,
            'minutes_per_game': self.minutes_per_game,
            'points_per_game': self.points_per_game,
            'rebounds_per_game': self.rebounds_per_game,
            'assists_per_game': self.assists_per_game,
            'steals_per_game': self.steals_per_game,
            'blocks_per_game': self.blocks_per_game,
            'turnovers_per_game': self.turnovers_per_game,
            'field_goal_pct': self.field_goal_pct,
            'three_point_pct': self.three_point_pct,
            'free_throw_pct': self.free_throw_pct,
            'plus_minus': self.plus_minus
        }