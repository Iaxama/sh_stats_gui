from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGridLayout, QCheckBox, QRadioButton,
    QButtonGroup, QFrame, QSizePolicy, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import storage
from models.player import Player
from models.game import Game, PlayerResult
from ui.player_tooltip import PlayerWidget
from ui.theme import GOLD, TEXT, CARD, BORDER, RED, SURFACE, TEXT_DIM, BG


# ── Per-player card ────────────────────────────────────────────────────────

class PlayerCard(QWidget):
    """One card per player: avatar, name, role radios, died checkbox."""

    ROLES = [("Liberal", "liberal"), ("Fascist", "fascist"), ("Hitler", "hitler")]

    def __init__(self, player: Player, parent=None):
        super().__init__(parent)
        self.player = player

        self.setFixedWidth(148)
        self.setStyleSheet(
            f"background-color: {CARD}; border: 1px solid {BORDER}; border-radius: 6px;"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(4)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        pw = PlayerWidget(player, avatar_size=72)
        pw.setStyleSheet("background: transparent; border: none;")
        pw.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(pw, alignment=Qt.AlignmentFlag.AlignCenter)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; border: none; background: {BORDER}; max-height: 1px;")
        root.addWidget(sep)

        # Role radio buttons
        role_lbl = QLabel("Role")
        role_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent; border: none;")
        role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(role_lbl)

        self._role_group = QButtonGroup(self)
        self._role_group.setExclusive(False)
        for label, value in self.ROLES:
            rb = QRadioButton(label)
            rb.setProperty("roleValue", value)
            rb.setStyleSheet("font-size: 12px; background: transparent; border: none;")
            self._role_group.addButton(rb)
            root.addWidget(rb)
            rb.clicked.connect(self._on_role_clicked)

        # Died checkbox
        self._died_cb = QCheckBox("Died")
        self._died_cb.setStyleSheet("font-size: 12px; background: transparent; border: none;")
        root.addWidget(self._died_cb)

        self._set_controls_enabled(False)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _set_controls_enabled(self, enabled: bool) -> None:
        self._died_cb.setEnabled(enabled)
        self.setStyleSheet(
            f"background-color: {CARD if enabled else SURFACE}; "
            f"border: 1px solid {'#8b0000' if enabled else BORDER}; border-radius: 6px;"
        )

    def _on_role_clicked(self, checked: bool) -> None:
        sender = self.sender()
        # uncheck all others to simulate exclusivity; allow toggling off
        for btn in self._role_group.buttons():
            if btn is not sender:
                btn.setChecked(False)
        playing = any(btn.isChecked() for btn in self._role_group.buttons())
        self._set_controls_enabled(playing)
        if not playing:
            self._died_cb.setChecked(False)

    # ── Public API ─────────────────────────────────────────────────────────

    def is_playing(self) -> bool:
        return any(btn.isChecked() for btn in self._role_group.buttons())

    def selected_role(self) -> Optional[str]:
        btn = self._role_group.checkedButton()
        return btn.property("roleValue") if btn else None

    def died(self) -> bool:
        return self._died_cb.isChecked()


# ── Main dialog ────────────────────────────────────────────────────────────

class AddGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Game Results")
        self.setMinimumSize(700, 620)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Title
        title = QLabel("Record Game Result")
        title.setFont(QFont("Georgia", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {GOLD};")
        root.addWidget(title)

        # Player grid inside scroll area
        players_lbl = QLabel("Select players and assign roles:")
        players_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-style: italic;")
        root.addWidget(players_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(320)

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(10)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._grid_widget)
        root.addWidget(scroll)

        self._cards: list[PlayerCard] = []
        self._populate_cards()

        # ── Outcome section ────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        root.addWidget(sep)

        outcome_row = QHBoxLayout()
        outcome_row.setSpacing(30)

        # Winning team
        team_box = QVBoxLayout()
        team_lbl = QLabel("Winning Team")
        team_lbl.setFont(QFont("Georgia", 12, QFont.Weight.Bold))
        team_lbl.setStyleSheet(f"color: {GOLD};")
        team_box.addWidget(team_lbl)

        self._team_group = QButtonGroup(self)
        self._rb_liberal = QRadioButton("Liberal")
        self._rb_fascist = QRadioButton("Fascist")
        self._team_group.addButton(self._rb_liberal)
        self._team_group.addButton(self._rb_fascist)
        team_box.addWidget(self._rb_liberal)
        team_box.addWidget(self._rb_fascist)
        outcome_row.addLayout(team_box)

        # Winning condition
        cond_box = QVBoxLayout()
        cond_lbl = QLabel("Winning Condition")
        cond_lbl.setFont(QFont("Georgia", 12, QFont.Weight.Bold))
        cond_lbl.setStyleSheet(f"color: {GOLD};")
        cond_box.addWidget(cond_lbl)

        self._cond_group = QButtonGroup(self)
        self._rb_policies  = QRadioButton("Enough Policies Enacted")
        self._rb_elected   = QRadioButton("Hitler Elected Chancellor")
        self._rb_executed  = QRadioButton("Hitler Executed")
        for rb in (self._rb_policies, self._rb_elected, self._rb_executed):
            self._cond_group.addButton(rb)
            cond_box.addWidget(rb)
        outcome_row.addLayout(cond_box)
        outcome_row.addStretch()

        root.addLayout(outcome_row)

        # Wire team → condition availability
        self._rb_liberal.toggled.connect(self._update_conditions)
        self._rb_fascist.toggled.connect(self._update_conditions)
        self._update_conditions()

        # Error + save
        self._error_frame = QFrame()
        self._error_frame.setStyleSheet(
            f"background-color: #2a0a0a; border: 1px solid {RED}; border-radius: 4px; padding: 2px;"
        )
        self._error_frame.setVisible(False)
        err_frame_layout = QVBoxLayout(self._error_frame)
        err_frame_layout.setContentsMargins(10, 6, 10, 6)
        self._error_lbl = QLabel("")
        self._error_lbl.setStyleSheet(f"color: #ff6b6b; background: transparent; border: none;")
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_lbl.setWordWrap(True)
        err_frame_layout.addWidget(self._error_lbl)
        root.addWidget(self._error_frame)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Game")
        save_btn.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    # ── Setup ──────────────────────────────────────────────────────────────

    def _populate_cards(self) -> None:
        players = storage.load_players()
        cols = 4
        for i, player in enumerate(players):
            card = PlayerCard(player)
            self._cards.append(card)
            self._grid_layout.addWidget(card, i // cols, i % cols)

        if not players:
            empty = QLabel("No players registered yet. Add players first.")
            empty.setStyleSheet(f"color: {TEXT_DIM}; font-style: italic;")
            self._grid_layout.addWidget(empty, 0, 0)

    def _set_error(self, msg: str) -> None:
        self._error_lbl.setText(msg)
        self._error_frame.setVisible(bool(msg))

    # ── Logic ──────────────────────────────────────────────────────────────

    def _update_conditions(self) -> None:
        liberal_wins = self._rb_liberal.isChecked()
        fascist_wins = self._rb_fascist.isChecked()

        # Hitler Elected → only valid for Fascist win
        self._rb_elected.setEnabled(fascist_wins)
        if not fascist_wins and self._rb_elected.isChecked():
            self._rb_elected.setChecked(False)

        # Hitler Executed → only valid for Liberal win
        self._rb_executed.setEnabled(liberal_wins)
        if not liberal_wins and self._rb_executed.isChecked():
            self._rb_executed.setChecked(False)

    def _save(self) -> None:
        playing = [(c, c.selected_role()) for c in self._cards if c.is_playing()]

        if len(playing) < 2:
            self._set_error("At least 2 players must be marked as playing.")
            return

        no_role = [c.player.name for c, r in playing if r is None]
        if no_role:
            self._set_error(f"Missing role for: {', '.join(no_role)}")
            return

        hitlers = [c for c, r in playing if r == "hitler"]
        if len(hitlers) != 1:
            self._set_error("Exactly one player must be assigned the Hitler role.")
            return

        # floor((n-1)/2) - 1 fascists (not counting Hitler); min 5 players
        n = len(playing)
        if n < 5:
            self._set_error(f"Invalid player count ({n}). Secret Hitler requires at least 5 players.")
            return
        expected_fascists = (n - 1) // 2 - 1
        expected_liberals = n - expected_fascists - 1
        fascist_count = sum(1 for _, r in playing if r == "fascist")
        liberal_count = sum(1 for _, r in playing if r == "liberal")
        if fascist_count != expected_fascists:
            self._set_error(
                f"With {n} players, there must be exactly {expected_fascists} Fascist(s) "
                f"(+ Hitler). Got {fascist_count}."
            )
            return
        if liberal_count != expected_liberals:
            self._set_error(
                f"With {n} players, there must be exactly {expected_liberals} Liberal(s). Got {liberal_count}."
            )
            return

        winning_team = (
            "liberal" if self._rb_liberal.isChecked() else
            "fascist" if self._rb_fascist.isChecked() else None
        )
        if winning_team is None:
            self._set_error("Select a winning team.")
            return

        winning_condition = (
            "policies_enacted" if self._rb_policies.isChecked() else
            "hitler_elected"   if self._rb_elected.isChecked() else
            "hitler_executed"  if self._rb_executed.isChecked() else None
        )
        if winning_condition is None:
            self._set_error("Select a winning condition.")
            return

        results = [
            PlayerResult(player_id=c.player.id, role=r, died=c.died())
            for c, r in playing
        ]
        game = Game(
            players=results,
            winning_team=winning_team,
            winning_condition=winning_condition,
            date=datetime.now(timezone.utc).isoformat(),
        )
        games = storage.load_games()
        games.append(game)
        storage.save_games(games)
        self.accept()
