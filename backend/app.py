from __future__ import annotations
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from backend.routes.players import players_bp, set_git_sync as set_players_git_sync
from backend.routes.games import games_bp, set_git_sync as set_games_git_sync
from backend.git_sync import GitSync, GitSyncError, GitAuthError, GitMergeConflictError

# Configure logging
logging.basicConfig(
    level=os.getenv("GIT_SYNC_DEBUG") and logging.DEBUG or logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
)

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_FRONTEND_DIST = os.path.join(_ROOT, "frontend", "dist")
_DATA_DIR = os.path.join(_ROOT, "data")
_AVATARS_DIR = os.path.join(_DATA_DIR, "assets", "avatars")

# Global git sync instance
_git_sync: GitSync | None = None


def _initialize_git_sync() -> GitSync | None:
    """Initialize git sync if configured via environment variables.
    
    Supports two authentication methods:
    1. SSH: GIT_DATA_REPO_URL (SSH URL) + GIT_SSH_KEY_PATH (optional, defaults to ~/.ssh/id_rsa)
    2. HTTPS with PAT: GIT_DATA_REPO_URL (HTTPS URL) + GIT_GITHUB_TOKEN (required)
    """
    repo_url = os.getenv("GIT_DATA_REPO_URL")
    if not repo_url:
        return None

    try:
        git_sync = GitSync(
            data_dir=_DATA_DIR,
            repo_url=repo_url,
            ssh_key_path=os.getenv("GIT_SSH_KEY_PATH"),
            github_token=os.getenv("GIT_GITHUB_TOKEN"),
            author_name=os.getenv("GIT_AUTHOR_NAME", "Data Sync"),
            author_email=os.getenv("GIT_AUTHOR_EMAIL", "sync@example.com"),
        )
        return git_sync
    except Exception as e:
        logging.warning(f"Failed to initialize git sync: {e}")
        return None


def create_app() -> Flask:
    global _git_sync

    app = Flask(__name__, static_folder=_FRONTEND_DIST, static_url_path="")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize git sync
    _git_sync = _initialize_git_sync()
    if _git_sync:
        logging.info("Git sync enabled")
        set_players_git_sync(_git_sync)
        set_games_git_sync(_git_sync)
    else:
        logging.info("Git sync disabled (GIT_DATA_REPO_URL not set)")

    app.register_blueprint(players_bp)
    app.register_blueprint(games_bp)

    @app.route("/avatars/<path:filename>")
    def serve_avatar(filename: str):
        return send_from_directory(_AVATARS_DIR, filename)

    @app.route("/api/sync/pull", methods=["GET"])
    def sync_pull():
        """Pull latest data from remote repository."""
        if not _git_sync:
            return jsonify({"error": "Git sync not configured"}), 503

        try:
            result = _git_sync.clone_or_pull()
            return jsonify(result), 200
        except GitAuthError as e:
            return jsonify({"error": "SSH authentication failed", "details": str(e)}), 401
        except GitSyncError as e:
            return jsonify({"error": "Git sync failed", "details": str(e)}), 500

    @app.route("/api/sync/status", methods=["GET"])
    def sync_status():
        """Get current sync status."""
        if not _git_sync:
            return jsonify({"error": "Git sync not configured"}), 503

        try:
            status = _git_sync.get_status()
            return jsonify(status), 200
        except Exception as e:
            return jsonify({"error": "Failed to get status", "details": str(e)}), 500

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path: str):
        full = os.path.join(_FRONTEND_DIST, path)
        if path and os.path.exists(full):
            return send_from_directory(_FRONTEND_DIST, path)
        return send_from_directory(_FRONTEND_DIST, "index.html")

    return app
