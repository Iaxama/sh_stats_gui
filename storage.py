from __future__ import annotations
import calendar
import json
import os
import shutil
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from models.player import Player
from models.game import Game
from models.season import Season

if TYPE_CHECKING:
    from backend.git_sync import GitSync

_BASE = os.path.join(os.path.dirname(__file__))
DATA_DIR    = os.path.join(_BASE, "data")
ASSETS_DIR  = os.path.join(DATA_DIR, "assets")
AVATARS_DIR = os.path.join(ASSETS_DIR, "avatars")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")
GAMES_FILE   = os.path.join(DATA_DIR, "games.json")
SEASONS_FILE = os.path.join(DATA_DIR, "seasons.json")
SEASON_MONTHS = 3


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


def season_end_for(start: datetime, months: int = SEASON_MONTHS) -> datetime:
    """Last moment of the month that closes a season starting at `start`."""
    index = start.year * 12 + (start.month - 1) + (months - 1)
    year, month = divmod(index, 12)
    month += 1
    last_day = calendar.monthrange(year, month)[1]
    return datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)


def load_seasons_raw() -> List[Season]:
    _ensure_dirs()
    if not os.path.exists(SEASONS_FILE):
        return []
    with open(SEASONS_FILE, "r", encoding="utf-8") as f:
        return [Season.from_dict(d) for d in json.load(f)]


def save_seasons(seasons: List[Season], git_sync: Optional[GitSync] = None) -> None:
    _ensure_dirs()
    with open(SEASONS_FILE, "w", encoding="utf-8") as f:
        json.dump([s.to_dict() for s in seasons], f, indent=2)

    if git_sync:
        git_sync.push("Update seasons data")


def ensure_seasons(git_sync: Optional[GitSync] = None) -> List[Season]:
    """Load seasons, creating Season 1 from existing games on first run."""
    seasons = load_seasons_raw()
    games = load_games()
    if not seasons:
        now = datetime.now(timezone.utc)
        dates = sorted(g.date for g in games if g.date)
        start = dates[0] if dates else now.isoformat()
        seasons = [Season(number=1, start_date=start,
                          scheduled_end=season_end_for(now, 1).isoformat())]
        save_seasons(seasons)
    current = next((s for s in seasons if s.end_date is None), seasons[-1])
    orphans = [g for g in games if not g.season_id]
    if orphans:
        for g in orphans:
            g.season_id = current.id
        save_games(games)
    return seasons


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
