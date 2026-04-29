import os

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    socketio.run(
        app,
        host=host,
        port=port,
        debug=app.config["DEBUG"],
        use_reloader=False,
    )
