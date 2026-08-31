from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor, QPainterPath
from PyQt6.QtCore import Qt, QSize

from ui.theme import SURFACE, GOLD_DIM


def make_circular_pixmap(source_path: str | None, size: int,
                         crop: dict | None = None) -> QPixmap:
    """Return a circular cropped pixmap, or a silhouette placeholder."""
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)

    if source_path:
        src = QPixmap(source_path)
        if not src.isNull():
            if crop:
                zoom   = crop["zoom"]
                ox     = crop["offset_x"]
                oy     = crop["offset_y"]
                cr     = crop["circle_r"]
                ps     = crop["preview_size"]
                cx = cy = ps / 2
                # region of original image that maps to the crop circle
                src_x    = (cx - cr - ox) / zoom
                src_y    = (cy - cr - oy) / zoom
                src_dim  = (2 * cr) / zoom
                src = src.copy(int(src_x), int(src_y), int(src_dim), int(src_dim))
            src = src.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)
            x = (src.width() - size) // 2
            y = (src.height() - size) // 2
            painter.drawPixmap(0, 0, src, x, y, size, size)
            painter.end()
            return result

    # silhouette placeholder
    painter.setBrush(QBrush(QColor(SURFACE)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    # simple head + body shape
    painter.setBrush(QBrush(QColor(GOLD_DIM)))
    head_r = size // 5
    cx = size // 2
    painter.drawEllipse(cx - head_r, size // 6, head_r * 2, head_r * 2)
    painter.drawEllipse(cx - size // 3, size // 2, (size // 3) * 2, size // 2)
    painter.end()
    return result


def avatar_label(source_path: str | None, size: int,
                 crop: dict | None = None) -> QLabel:
    lbl = QLabel()
    lbl.setFixedSize(QSize(size, size))
    lbl.setPixmap(make_circular_pixmap(source_path, size, crop))
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl
