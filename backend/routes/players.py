from __future__ import annotations
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Blueprint, jsonify, request
from filelock import FileLock

import storage
from models.player import Player

if False:
    from backend.git_sync import GitSync

players_bp = Blueprint("players", __name__)

_lock = FileLock(os.path.join(os.path.dirname(__file__), "..", "..", "data", "players.lock"))
_git_sync: Optional[GitSync] = None


def set_git_sync(git_sync: GitSync) -> None:
    """Set the global git sync instance."""
    global _git_sync
    _git_sync = git_sync


@players_bp.get("/api/players")
def list_players():
    return jsonify([p.to_dict() for p in storage.load_players()])


@players_bp.post("/api/players")
def create_player():
    from backend.git_sync import GitMergeConflictError
    
    data = request.get_json(force=True)
    player = Player(name=data["name"])
    with _lock:
        players = storage.load_players()
        players.append(player)
        try:
            storage.save_players(players, git_sync=_git_sync)
        except GitMergeConflictError as e:
            return jsonify({"error": "Merge conflict", "details": str(e)}), 409
    return jsonify(player.to_dict()), 201


@players_bp.put("/api/players/<player_id>")
def update_player(player_id: str):
    from backend.git_sync import GitMergeConflictError
    
    data = request.get_json(force=True)
    with _lock:
        players = storage.load_players()
        for p in players:
            if p.id == player_id:
                p.name = data.get("name", p.name)
                p.avatar_crop = data.get("avatar_crop", p.avatar_crop)
                try:
                    storage.save_players(players, git_sync=_git_sync)
                except GitMergeConflictError as e:
                    return jsonify({"error": "Merge conflict", "details": str(e)}), 409
                return jsonify(p.to_dict())
    return jsonify({"error": "not found"}), 404


@players_bp.delete("/api/players/<player_id>")
def delete_player(player_id: str):
    from backend.git_sync import GitMergeConflictError
    
    with _lock:
        players = storage.load_players()
        remaining = [p for p in players if p.id != player_id]
        if len(remaining) == len(players):
            return jsonify({"error": "not found"}), 404
        deleted = next(p for p in players if p.id == player_id)
        if deleted.avatar_path:
            storage.delete_avatar(deleted.avatar_path)
        try:
            storage.save_players(remaining, git_sync=_git_sync)
        except GitMergeConflictError as e:
            return jsonify({"error": "Merge conflict", "details": str(e)}), 409
    return "", 204


@players_bp.post("/api/players/<player_id>/avatar")
def upload_avatar(player_id: str):
    from backend.git_sync import GitMergeConflictError
    
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
                try:
                    storage.save_players(players, git_sync=_git_sync)
                except GitMergeConflictError as e:
                    return jsonify({"error": "Merge conflict", "details": str(e)}), 409
                return jsonify({"avatar_path": relative})
    return jsonify({"error": "not found"}), 404
