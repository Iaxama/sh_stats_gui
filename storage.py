from __future__ import annotations
import json
import os
import shutil
from typing import List, Optional, TYPE_CHECKING

from models.player import Player
from models.game import Game

if TYPE_CHECKING:
    from backend.git_sync import GitSync

_BASE = os.path.join(os.path.dirname(__file__))
DATA_DIR    = os.path.join(_BASE, "data")
ASSETS_DIR  = os.path.join(DATA_DIR, "assets")
AVATARS_DIR = os.path.join(ASSETS_DIR, "avatars")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")
GAMES_FILE   = os.path.join(DATA_DIR, "games.json")


def _ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(AVATARS_DIR, exist_ok=True)


def load_players() -> List[Player]:
    _ensure_dirs()
    if not os.path.exists(PLAYERS_FILE):
        return []
    with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
        return [Player.from_dict(d) for d in json.load(f)]


def save_players(players: List[Player], git_sync: Optional[GitSync] = None) -> None:
    _ensure_dirs()
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in players], f, indent=2)
    
    if git_sync:
        git_sync.push("Update players data")


def load_games() -> List[Game]:
    _ensure_dirs()
    if not os.path.exists(GAMES_FILE):
        return []
    with open(GAMES_FILE, "r", encoding="utf-8") as f:
        return [Game.from_dict(d) for d in json.load(f)]


def save_games(games: List[Game], git_sync: Optional[GitSync] = None) -> None:
    _ensure_dirs()
    with open(GAMES_FILE, "w", encoding="utf-8") as f:
        json.dump([g.to_dict() for g in games], f, indent=2)
    
    if git_sync:
        git_sync.push("Update games data")


def copy_avatar(src_path: str) -> str:
    """Copy an image into the Git-tracked assets/avatars directory."""
    _ensure_dirs()
    ext = os.path.splitext(src_path)[1]
    filename = f"{os.urandom(8).hex()}{ext}"
    dest = os.path.join(AVATARS_DIR, filename)
    shutil.copy2(src_path, dest)
    return os.path.join("assets", "avatars", filename)


def resolve_avatar(relative_path: str) -> str:
    return os.path.join(DATA_DIR, relative_path)


def delete_avatar(relative_path: str) -> None:
    """Remove an avatar file from disk; silently ignores missing files."""
    try:
        os.remove(resolve_avatar(relative_path))
    except FileNotFoundError:
        pass
