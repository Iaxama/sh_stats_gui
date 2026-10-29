from __future__ import annotations
import os
import sys
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Blueprint, jsonify, request
from filelock import FileLock

import storage
from backend.awards import compute_awards
from backend.routes.players import _lock as _players_lock
from backend.routes.games import _lock as _games_lock
from models.season import Season

if False:
    from backend.git_sync import GitSync

seasons_bp = Blueprint("seasons", __name__)

_lock = FileLock(os.path.join(os.path.dirname(__file__), "..", "..", "data", "seasons.lock"))
_git_sync: Optional[GitSync] = None


def set_git_sync(git_sync: GitSync) -> None:
    global _git_sync
    _git_sync = git_sync


@seasons_bp.get("/api/seasons")
def list_seasons():
    with _lock, _games_lock:
        seasons = storage.ensure_seasons()
    return jsonify([s.to_dict() for s in seasons])


@seasons_bp.post("/api/seasons")
def start_new_season():
    """End the current season (freezing its awards), retire players and start the next one."""
    from backend.git_sync import GitMergeConflictError

    data = request.get_json(silent=True) or {}
    retire_ids = set(data.get("retire_ids") or [])

    with _lock, _games_lock, _players_lock:
        seasons = storage.ensure_seasons()
        current = next((s for s in seasons if s.end_date is None), seasons[-1])
        games = [g for g in storage.load_games() if g.season_id == current.id]
        now = datetime.now(timezone.utc)

        current.end_date = now.isoformat()
        current.awards = compute_awards(games)
        new_season = Season(
            number=max(s.number for s in seasons) + 1,
            start_date=now.isoformat(),
            scheduled_end=storage.season_end_for(now).isoformat(),
        )
        seasons.append(new_season)

        if retire_ids:
            players = storage.load_players()
            for p in players:
                if p.id in retire_ids:
                    p.retired = True
            storage.save_players(players)
        try:
            storage.save_seasons(seasons, git_sync=_git_sync)
        except GitMergeConflictError as e:
            return jsonify({"error": "Merge conflict", "details": str(e)}), 409
    return jsonify([s.to_dict() for s in seasons]), 201
