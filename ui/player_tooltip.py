from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QApplication,
    QDialog, QPushButton, QGridLayout, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QEvent, QPoint, QObject, QSize
from PyQt6.QtGui import QFont, QCursor, QPixmap

import storage
from ui.avatar import make_circular_pixmap
from ui.theme import GOLD, GOLD_DIM, TEXT_DIM, BORDER, SURFACE


def _compute_player_stats(player_id: str) -> dict:
    games = storage.load_games()
    s = {
        "played": 0,
        "liberal": 0, "fascist": 0, "hitler": 0,
        "wins": 0, "losses": 0, "deaths": 0,
        "lib_wins": 0, "fas_wins": 0, "hit_wins": 0,
    }
    for game in games:
        for pr in game.players:
            if pr.player_id != player_id:
                continue
            s["played"] += 1
            s[pr.role] += 1
            if pr.died:
                s["deaths"] += 1
            won = (pr.role == "liberal" and game.winning_team == "liberal") or \
                  (pr.role in ("fascist", "hitler") and game.winning_team == "fascist")
            if won:
                s["wins"] += 1
                s[f"{pr.role[:3]}_wins"] += 1  # lib_wins / fas_wins / hit_wins
            else:
                s["losses"] += 1
    return s


def _pct(wins: int, total: int) -> str:
    return f"{wins / total * 100:.0f}%" if total else "—"


class _PlayerPopup(QFrame):
    """Singleton tooltip popup shown when hovering a PlayerWidget."""

    def __init__(self) -> None:
        super().__init__(None, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(
            f"QFrame {{ background: {SURFACE}; border: 1px solid {GOLD_DIM};"
            f" border-radius: 8px; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        self._avatar_lbl = QLabel()
        self._avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar_lbl.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self._avatar_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self._name_lbl = QLabel()
        self._name_lbl.setFont(QFont("Georgia", 13, QFont.Weight.Bold))
        self._name_lbl.setStyleSheet(f"color: {GOLD}; border: none; background: transparent;")
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._name_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {BORDER}; max-height: 1px; border: none;")
        layout.addWidget(sep)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(18)
        self._lib_lbl  = self._stat_label("Liberal")
        self._fas_lbl  = self._stat_label("Fascist")
        self._winr_lbl = self._stat_label("Win rate")
        for w in (self._lib_lbl, self._fas_lbl, self._winr_lbl):
            stats_row.addWidget(w)
        layout.addLayout(stats_row)

    @staticmethod
    def _stat_label(caption: str) -> QLabel:
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("border: none; background: transparent;")
        lbl.setProperty("_caption", caption)
        return lbl

    def _set_stat(self, lbl: QLabel, value: str) -> None:
        caption = lbl.property("_caption")
        lbl.setText(
            f"<div style='text-align:center'>"
            f"<span style='font-size:16px;font-weight:bold;color:{GOLD}'>{value}</span>"
            f"<br/><span style='font-size:10px;color:{TEXT_DIM}'>{caption}</span>"
            f"</div>"
        )

    def load(self, player) -> None:
        avatar_path = storage.resolve_avatar(player.avatar_path) if player.avatar_path else None
        self._avatar_lbl.setPixmap(
            make_circular_pixmap(avatar_path, 80, getattr(player, "avatar_crop", None))
        )
        self._name_lbl.setText(player.name)
        s = _compute_player_stats(player.id)
        self._set_stat(self._lib_lbl,  str(s["liberal"]))
        self._set_stat(self._fas_lbl,  str(s["fascist"]))
        self._set_stat(self._winr_lbl, _pct(s["wins"], s["played"]))
        self.adjustSize()


_popup: _PlayerPopup | None = None


def _get_popup() -> _PlayerPopup:
    global _popup
    if _popup is None:
        _popup = _PlayerPopup()
    return _popup


class _HoverFilter(QObject):
    def __init__(self, widget: QWidget, player) -> None:
        super().__init__(widget)
        self._widget = widget
        self._player = player

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Enter:
            popup = _get_popup()
            popup.load(self._player)
            pos = self._widget.mapToGlobal(QPoint(0, self._widget.height() + 4))
            screen = QApplication.primaryScreen().geometry()
            pw = popup.sizeHint().width()
            ph = popup.sizeHint().height()
            x = min(pos.x(), screen.right() - pw - 4)
            y = min(pos.y(), screen.bottom() - ph - 4)
            popup.move(x, y)
            popup.show()
            popup.raise_()
        elif event.type() in (QEvent.Type.Leave, QEvent.Type.Hide,
                              QEvent.Type.MouseButtonPress):
            _get_popup().hide()
        return False


class _FullImageDialog(QDialog):
    """Lightbox showing the original uncropped avatar at a comfortable size."""

    def __init__(self, image_path: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Profile picture")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        src = QPixmap(image_path)
        screen = QApplication.primaryScreen().availableGeometry()
        max_w = int(screen.width()  * 0.8)
        max_h = int(screen.height() * 0.8)
        if src.width() > max_w or src.height() > max_h:
            src = src.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel()
        lbl.setPixmap(src)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.mousePressEvent = lambda _: (self.accept(), None)[1]
        lbl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout.addWidget(lbl)
        self.adjustSize()


class PlayerProfileDialog(QDialog):
    """Full-stats modal opened when clicking a PlayerWidget."""

    def __init__(self, player, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(player.name)
        self.setMinimumWidth(340)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Avatar — clickable if a source image exists
        avatar_path = storage.resolve_avatar(player.avatar_path) if player.avatar_path else None
        av = QLabel()
        av.setPixmap(make_circular_pixmap(avatar_path, 96, getattr(player, "avatar_crop", None)))
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet("border: none; background: transparent;")
        if avatar_path:
            av.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            av.setToolTip("Click to view full picture")
            av.mousePressEvent = lambda _, p=avatar_path: (_FullImageDialog(p, self).exec(), None)[1]
        root.addWidget(av)

        name_lbl = QLabel(player.name)
        name_lbl.setFont(QFont("Georgia", 16, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(f"color: {GOLD};")
        root.addWidget(name_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {BORDER}; max-height: 1px; border: none;")
        root.addWidget(sep)

        s = _compute_player_stats(player.id)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)

        rows = [
            ("Games played",   str(s["played"])),
            ("Wins",           str(s["wins"])),
            ("Losses",         str(s["losses"])),
            ("Deaths",         str(s["deaths"])),
            ("— as Liberal",   f"{s['liberal']}  ({_pct(s['lib_wins'], s['liberal'])})"),
            ("— as Fascist",   f"{s['fascist']}  ({_pct(s['fas_wins'], s['fascist'])})"),
            ("— as Hitler",    f"{s['hitler']}  ({_pct(s['hit_wins'], s['hitler'])})"),
            ("Overall win %",  _pct(s["wins"], s["played"])),
        ]

        for i, (label, value) in enumerate(rows):
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {TEXT_DIM};")
            val = QLabel(value)
            val.setStyleSheet(f"color: {GOLD}; font-weight: bold;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)

        root.addLayout(grid)

        close_btn = QPushButton("Close")
        close_btn.setMaximumWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)


class PlayerWidget(QWidget):
    """Avatar + optional name label; hover shows quick stats, click opens full profile."""

    def __init__(self, player, avatar_size: int = 44,
                 show_name: bool = True, parent=None) -> None:
        super().__init__(parent)
        self._player = player
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        avatar_path = storage.resolve_avatar(player.avatar_path) if player.avatar_path else None
        av = QLabel()
        av.setPixmap(make_circular_pixmap(avatar_path, avatar_size,
                                          getattr(player, "avatar_crop", None)))
        av.setFixedSize(QSize(avatar_size, avatar_size))
        av.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(av)

        if show_name:
            name_lbl = QLabel(player.name)
            name_lbl.setStyleSheet(f"color: {GOLD}; background: transparent; border: none;")
            layout.addWidget(name_lbl)

        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        _f = _HoverFilter(self, player)
        _f.setParent(self)
        self.installEventFilter(_f)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            _get_popup().hide()
            PlayerProfileDialog(self._player, self).exec()
        super().mousePressEvent(event)
