from __future__ import annotations
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Blueprint, jsonify, request
from filelock import FileLock

import storage
from models.game import Game, PlayerResult

games_bp = Blueprint("games", __name__)

_lock = FileLock(os.path.join(os.path.dirname(__file__), "..", "..", "data", "games.lock"))


@games_bp.get("/api/games")
def list_games():
    return jsonify([g.to_dict() for g in storage.load_games()])


@games_bp.post("/api/games")
def create_game():
    data = request.get_json(force=True)
    game = Game(
        players=[PlayerResult.from_dict(p) for p in data["players"]],
        winning_team=data["winning_team"],
        winning_condition=data["winning_condition"],
        date=data.get("date", datetime.now(timezone.utc).isoformat()),
    )
    with _lock:
        games = storage.load_games()
        games.append(game)
        storage.save_games(games)
    return jsonify(game.to_dict()), 201


@games_bp.delete("/api/games/<game_id>")
def delete_game(game_id: str):
    with _lock:
        games = storage.load_games()
        remaining = [g for g in games if g.id != game_id]
        if len(remaining) == len(games):
            return jsonify({"error": "not found"}), 404
        storage.save_games(remaining)
    return "", 204
