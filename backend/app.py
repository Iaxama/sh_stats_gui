from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, send_from_directory
from flask_cors import CORS

from backend.routes.players import players_bp
from backend.routes.games import games_bp

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_FRONTEND_DIST = os.path.join(_ROOT, "frontend", "dist")
_AVATARS_DIR = os.path.join(_ROOT, "assets", "avatars")


def create_app() -> Flask:
    app = Flask(__name__, static_folder=_FRONTEND_DIST, static_url_path="")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(players_bp)
    app.register_blueprint(games_bp)

    @app.route("/avatars/<path:filename>")
    def serve_avatar(filename: str):
        return send_from_directory(_AVATARS_DIR, filename)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path: str):
        full = os.path.join(_FRONTEND_DIST, path)
        if path and os.path.exists(full):
            return send_from_directory(_FRONTEND_DIST, path)
        return send_from_directory(_FRONTEND_DIST, "index.html")

    return app
