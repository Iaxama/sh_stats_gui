from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Blueprint, jsonify, request
from filelock import FileLock

import storage
from models.player import Player

players_bp = Blueprint("players", __name__)

_lock = FileLock(os.path.join(os.path.dirname(__file__), "..", "..", "data", "players.lock"))


@players_bp.get("/api/players")
def list_players():
    return jsonify([p.to_dict() for p in storage.load_players()])


@players_bp.post("/api/players")
def create_player():
    data = request.get_json(force=True)
    player = Player(name=data["name"])
    with _lock:
        players = storage.load_players()
        players.append(player)
        storage.save_players(players)
    return jsonify(player.to_dict()), 201


@players_bp.put("/api/players/<player_id>")
def update_player(player_id: str):
    data = request.get_json(force=True)
    with _lock:
        players = storage.load_players()
        for p in players:
            if p.id == player_id:
                p.name = data.get("name", p.name)
                p.avatar_crop = data.get("avatar_crop", p.avatar_crop)
                storage.save_players(players)
                return jsonify(p.to_dict())
    return jsonify({"error": "not found"}), 404


@players_bp.delete("/api/players/<player_id>")
def delete_player(player_id: str):
    with _lock:
        players = storage.load_players()
        remaining = [p for p in players if p.id != player_id]
        if len(remaining) == len(players):
            return jsonify({"error": "not found"}), 404
        deleted = next(p for p in players if p.id == player_id)
        if deleted.avatar_path:
            storage.delete_avatar(deleted.avatar_path)
        storage.save_players(remaining)
    return "", 204


@players_bp.post("/api/players/<player_id>/avatar")
def upload_avatar(player_id: str):
    if "avatar" not in request.files:
        return jsonify({"error": "no file"}), 400
    file = request.files["avatar"]
    ext = os.path.splitext(file.filename)[1] or ".png"
    filename = f"{os.urandom(8).hex()}{ext}"
    dest = os.path.join(storage.AVATARS_DIR, filename)
    storage._ensure_dirs()
    file.save(dest)
    relative = os.path.join("assets", "avatars", filename)
    with _lock:
        players = storage.load_players()
        for p in players:
            if p.id == player_id:
                if p.avatar_path:
                    storage.delete_avatar(p.avatar_path)
                p.avatar_path = relative
                storage.save_players(players)
                return jsonify({"avatar_path": relative})
    return jsonify({"error": "not found"}), 404
