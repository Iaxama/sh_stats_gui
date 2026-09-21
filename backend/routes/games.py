from __future__ import annotations
import os
import sys
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Blueprint, jsonify, request
from filelock import FileLock

import storage
from models.game import Game, PlayerResult

if False:
    from backend.git_sync import GitSync

games_bp = Blueprint("games", __name__)

_lock = FileLock(os.path.join(os.path.dirname(__file__), "..", "..", "data", "games.lock"))
_git_sync: Optional[GitSync] = None


def set_git_sync(git_sync: GitSync) -> None:
    """Set the global git sync instance."""
    global _git_sync
    _git_sync = git_sync


@games_bp.get("/api/games")
def list_games():
    return jsonify([g.to_dict() for g in storage.load_games()])


@games_bp.post("/api/games")
def create_game():
    from backend.git_sync import GitMergeConflictError
    
    data = request.get_json(force=True)
    sniper_id = data.get("sniper_id")
    hitler_was_executed = (
        data.get("winning_team") == "liberal"
        and data.get("winning_condition") == "hitler_executed"
    )
    if hitler_was_executed:
        player_roles = {p["player_id"]: p["role"] for p in data.get("players", [])}
        if not sniper_id:
            return jsonify({"error": "Select the player who killed Hitler."}), 400
        if sniper_id not in player_roles or player_roles[sniper_id] == "hitler":
            return jsonify({"error": "The sniper must be a participating player other than Hitler."}), 400
    elif sniper_id:
        return jsonify({"error": "A sniper can only be recorded when Hitler is executed."}), 400

    game = Game(
        players=[PlayerResult.from_dict(p) for p in data["players"]],
        winning_team=data["winning_team"],
        winning_condition=data["winning_condition"],
        date=data.get("date", datetime.now(timezone.utc).isoformat()),
        sniper_id=sniper_id,
    )
    with _lock:
        games = storage.load_games()
        games.append(game)
        try:
            storage.save_games(games, git_sync=_git_sync)
        except GitMergeConflictError as e:
            return jsonify({"error": "Merge conflict", "details": str(e)}), 409
    return jsonify(game.to_dict()), 201


@games_bp.delete("/api/games/<game_id>")
def delete_game(game_id: str):
    from backend.git_sync import GitMergeConflictError
    
    with _lock:
        games = storage.load_games()
        remaining = [g for g in games if g.id != game_id]
        if len(remaining) == len(games):
            return jsonify({"error": "not found"}), 404
        try:
            storage.save_games(remaining, git_sync=_git_sync)
        except GitMergeConflictError as e:
            return jsonify({"error": "Merge conflict", "details": str(e)}), 409
    return "", 204
