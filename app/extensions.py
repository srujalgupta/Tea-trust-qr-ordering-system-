from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

try:
    from flask_migrate import Migrate
except ImportError:
    Migrate = None


class NoopMigrate:
    def init_app(self, app, db):
        app.logger.warning("Flask-Migrate is not installed; migration commands are unavailable.")


db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate() if Migrate else NoopMigrate()
