from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase


# ── Palette ────────────────────────────────────────────────────────────────
BG         = "#1a1a1a"
SURFACE    = "#242424"
CARD       = "#2b2020"
BORDER     = "#5a1010"
RED        = "#8b0000"
RED_HOVER  = "#c0392b"
GOLD       = "#c9a84c"
GOLD_DIM   = "#7a6030"
TEXT       = "#e8dcc8"
TEXT_DIM   = "#a09070"
DISABLED   = "#555555"

STYLESHEET = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Georgia", "Times New Roman", serif;
    font-size: 13px;
}}

QDialog, QMainWindow {{
    background-color: {BG};
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {RED};
    color: {TEXT};
    border: 1px solid {GOLD};
    border-radius: 4px;
    padding: 8px 18px;
    font-weight: bold;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background-color: {RED_HOVER};
    border-color: {GOLD};
}}
QPushButton:pressed {{
    background-color: #6b0000;
}}
QPushButton:disabled {{
    background-color: #3a2020;
    color: {DISABLED};
    border-color: #3a3030;
}}

/* ── Inputs ── */
QLineEdit, QTextEdit {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 8px;
    selection-background-color: {RED};
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {GOLD};
}}

/* ── ComboBox ── */
QComboBox {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 4px 8px;
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    color: {TEXT};
    selection-background-color: {RED};
    border: 1px solid {BORDER};
}}

/* ── CheckBox & RadioButton ── */
QCheckBox, QRadioButton {{
    color: {TEXT};
    spacing: 6px;
    background: transparent;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {GOLD_DIM};
    border-radius: 2px;
    background: {SURFACE};
}}
QRadioButton::indicator {{ border-radius: 7px; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {RED};
    border-color: {GOLD};
}}

/* ── ScrollArea ── */
QScrollArea {{
    border: none;
    background-color: {BG};
}}
QScrollBar:vertical {{
    background: {SURFACE};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── GroupBox ── */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: bold;
    color: {GOLD};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    color: {GOLD};
}}

/* ── Table ── */
QTableWidget {{
    background-color: {SURFACE};
    gridline-color: {BORDER};
    color: {TEXT};
    border: 1px solid {BORDER};
}}
QHeaderView::section {{
    background-color: {CARD};
    color: {GOLD};
    border: 1px solid {BORDER};
    padding: 4px;
    font-weight: bold;
}}
QTableWidget::item:selected {{
    background-color: {RED};
    color: {TEXT};
}}

/* ── Label ── */
QLabel {{
    background: transparent;
    color: {TEXT};
}}

/* ── Separator ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {BORDER};
}}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(STYLESHEET)
    # prefer a serif font if available on the system
    families = QFontDatabase.families()
    for candidate in ("IM Fell English", "Palatino Linotype", "Georgia", "Times New Roman"):
        if candidate in families:
            app.setFont(QFont(candidate, 12))
            break
