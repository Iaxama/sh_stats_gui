from __future__ import annotations
from datetime import datetime, timezone

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QSizePolicy, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

import storage
from models.game import Game
from models.player import Player
from ui.player_tooltip import PlayerWidget
from ui.theme import GOLD, TEXT, TEXT_DIM, RED, RED_HOVER, CARD, BORDER, SURFACE, BG


_CONDITION_LABEL = {
    "policies_enacted": "Policies Enacted",
    "hitler_elected":   "Hitler Elected",
    "hitler_executed":  "Hitler Executed",
}

_ROLE_COLOR = {
    "liberal": "#4a90d9",
    "fascist": "#c0392b",
    "hitler":  "#1a1a1a",
}
_ROLE_BG = {
    "liberal": "#1a3a5c",
    "fascist": "#4a1010",
    "hitler":  "#8b0000",
}


def _fmt_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone()
        return dt.strftime("%d %b %Y  %H:%M")
    except Exception:
        return iso


class GameCard(QFrame):
    """Collapsible card showing one game's summary."""

    def __init__(self, game: Game, players: dict[str, Player], index: int,
                 on_delete, parent=None):
        super().__init__(parent)
        self._game = game
        self._expanded = False

        self.setStyleSheet(
            f"QFrame#gameCard {{ background:{CARD}; border:1px solid {BORDER};"
            f" border-radius:6px; }}"
        )
        self.setObjectName("gameCard")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(0)

        # ── Header row (always visible) ────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(12)

        # Game number + date
        num_lbl = QLabel(f"Game #{index}")
        num_lbl.setFont(QFont("Georgia", 12, QFont.Weight.Bold))
        num_lbl.setStyleSheet(f"color: {GOLD}; background: transparent; border: none;")
        num_lbl.setFixedWidth(72)

        date_lbl = QLabel(_fmt_date(game.date))
        date_lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")

        # Winner badge
        team_color = "#4a90d9" if game.winning_team == "liberal" else "#c0392b"
        team_text  = "LIBERAL WIN" if game.winning_team == "liberal" else "FASCIST WIN"
        winner_lbl = QLabel(team_text)
        winner_lbl.setStyleSheet(
            f"color: {team_color}; font-weight: bold; font-size: 12px;"
            f" background: transparent; border: none;"
        )

        cond_lbl = QLabel(f"— {_CONDITION_LABEL.get(game.winning_condition, game.winning_condition)}")
        cond_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-style: italic; background: transparent; border: none;")

        self._toggle_btn = QPushButton("▼ Details")
        self._toggle_btn.setFixedWidth(88)
        self._toggle_btn.setStyleSheet(
            f"font-size: 11px; padding: 3px 8px; background: {SURFACE};"
            f" border: 1px solid {BORDER}; border-radius: 3px; color: {TEXT_DIM};"
        )
        self._toggle_btn.clicked.connect(self._toggle)

        del_btn = QPushButton("✕")
        del_btn.setFixedWidth(28)
        del_btn.setFixedHeight(24)
        del_btn.setStyleSheet(
            f"font-size: 11px; padding: 0; background: #3a1010;"
            f" border: 1px solid {BORDER}; border-radius: 3px; color: {TEXT_DIM};"
        )
        del_btn.setToolTip("Delete this game")
        del_btn.clicked.connect(lambda: on_delete(game.id))

        header.addWidget(num_lbl)
        header.addWidget(date_lbl)
        header.addStretch()
        header.addWidget(winner_lbl)
        header.addWidget(cond_lbl)
        header.addSpacing(12)
        header.addWidget(self._toggle_btn)
        header.addWidget(del_btn)
        outer.addLayout(header)

        # ── Detail panel (hidden by default) ─────────────────────────────
        self._detail = QWidget()
        self._detail.setStyleSheet("background: transparent;")
        detail_layout = QVBoxLayout(self._detail)
        detail_layout.setContentsMargins(0, 10, 0, 4)
        detail_layout.setSpacing(6)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; background: {BORDER}; max-height:1px; border:none;")
        detail_layout.addWidget(sep)

        # Player chips row
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        chips_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for pr in game.players:
            player = players.get(pr.player_id)
            name = player.name if player else "Unknown"

            chip = QFrame()
            chip.setStyleSheet(
                f"background: {_ROLE_BG[pr.role]}; border: 1px solid {BORDER};"
                f" border-radius: 5px;"
            )
            chip_layout = QVBoxLayout(chip)
            chip_layout.setContentsMargins(8, 6, 8, 6)
            chip_layout.setSpacing(3)
            chip_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if player:
                pw = PlayerWidget(player, avatar_size=40, show_name=False)
                pw.setStyleSheet("background: transparent; border: none;")
                chip_layout.addWidget(pw, alignment=Qt.AlignmentFlag.AlignCenter)
            else:
                av_lbl = QLabel()
                av_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                av_lbl.setStyleSheet("background: transparent; border: none;")
                chip_layout.addWidget(av_lbl)

            name_lbl = QLabel(name)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_lbl.setStyleSheet(
                f"color: {TEXT}; font-size: 11px; font-weight: bold;"
                f" background: transparent; border: none;"
            )

            role_lbl = QLabel(pr.role.capitalize())
            role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            role_lbl.setStyleSheet(
                f"color: {_ROLE_COLOR[pr.role]}; font-size: 10px;"
                f" background: transparent; border: none;"
            )

            extras = []
            if pr.died:
                extras.append("\u2020 died")
            if extras:
                extra_lbl = QLabel(" \u00b7 ".join(extras))
                extra_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                extra_lbl.setStyleSheet(
                    f"color: {TEXT_DIM}; font-size: 10px; font-style: italic;"
                    f" background: transparent; border: none;"
                )
                chip_layout.addWidget(extra_lbl)

            chip_layout.addWidget(name_lbl)
            chip_layout.addWidget(role_lbl)
            chips_row.addWidget(chip)

        chips_row.addStretch()
        detail_layout.addLayout(chips_row)

        self._detail.setVisible(False)
        outer.addWidget(self._detail)

    def _toggle(self):
        self._expanded = not self._expanded
        self._detail.setVisible(self._expanded)
        self._toggle_btn.setText("▲ Hide" if self._expanded else "▼ Details")


# ── History dialog ─────────────────────────────────────────────────────────

class GameHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game History")
        self.setMinimumSize(740, 540)

        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(24, 20, 24, 20)
        self._root.setSpacing(14)

        title = QLabel("Game History")
        title.setFont(QFont("Georgia", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {GOLD};")
        self._root.addWidget(title)

        self._players = {p.id: p for p in storage.load_players()}
        self._scroll_area = None
        self._build_list()

        close_btn = QPushButton("Close")
        close_btn.setMaximumWidth(120)
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        self._root.addLayout(btn_row)

    def _build_list(self) -> None:
        if self._scroll_area is not None:
            self._root.removeWidget(self._scroll_area)
            self._scroll_area.deleteLater()

        games = storage.load_games()
        games_sorted = sorted(games, key=lambda g: g.date, reverse=True)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if not games_sorted:
            empty = QLabel("No games recorded yet.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_DIM}; font-style: italic;")
            layout.addWidget(empty)
        else:
            for i, game in enumerate(games_sorted, start=1):
                # pass the total count so the displayed number is chronological
                chrono_index = len(games_sorted) - i + 1
                card = GameCard(game, self._players, chrono_index,
                                on_delete=self._confirm_delete)
                layout.addWidget(card)

        layout.addStretch()
        scroll.setWidget(container)
        # insert before the close-button row (last item)
        self._root.insertWidget(self._root.count() - 1, scroll)
        self._scroll_area = scroll

    def _confirm_delete(self, game_id: str) -> None:
        reply = QMessageBox.question(
            self, "Delete Game",
            "Permanently delete this game from history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        games = [g for g in storage.load_games() if g.id != game_id]
        storage.save_games(games)
        self._build_list()
