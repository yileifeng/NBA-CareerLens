import pytest

from src.app import app as flask_app

# configured Flask application for testing
@pytest.fixture()
def app():
    flask_app.config.update({
        "TESTING": True
    })
    
    yield flask_app
    
# Flask test client for making HTTP requests
@pytest.fixture()
def client(app):
    return app.test_client()
