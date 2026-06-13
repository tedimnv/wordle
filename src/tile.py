from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import (
    Property,
    QAbstractAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    Qt,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent
from PySide6.QtWidgets import QLabel, QWidget

from src.constants import LetterResult
from src.theme import (
    EMPTY_BG,
    EMPTY_BORDER,
    EMPTY_TEXT,
    REVEALED_TEXT,
    RESULT_BG,
    TILE_BORDER_PX,
    TILE_FONT_FAMILY,
    TILE_FONT_PX,
    TILE_SIZE_PX,
    TYPED_BORDER,
)

TYPE_IN_INITIAL_SCALE = 0.8


class Tile(QLabel):
    """A single Wordle tile. Owns its visuals and its own animations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(TILE_SIZE_PX, TILE_SIZE_PX)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._background = EMPTY_BG
        self._border = EMPTY_BORDER
        self._text_color = EMPTY_TEXT
        self._scale_value = 1.0
        self._flip_x_value = 1.0
        self._opacity_value = 1.0

    # ── Tell-only API: instant ───────────────────────────────────────────────
    def show_letter(self, letter: str) -> None:
        self._stop_active_anims()
        self.setText(letter.upper())
        self._border = TYPED_BORDER
        self._scale_value = 1.0
        self._flip_x_value = 1.0
        self._opacity_value = 1.0
        self.update()

    def clear(self) -> None:
        self._stop_active_anims()
        self.setText("")
        self._background = EMPTY_BG
        self._border = EMPTY_BORDER
        self._text_color = EMPTY_TEXT
        self._scale_value = 1.0
        self._flip_x_value = 1.0
        self._opacity_value = 1.0
        self.update()

    def reveal(self, result: LetterResult) -> None:
        # Note: does NOT stop active animations or reset transform values —
        # this method is called from the flip midpoint where flip_x must
        # stay at 0.
        color = RESULT_BG[result]
        self._background = color
        self._border = color
        self._text_color = REVEALED_TEXT
        self.update()

    # ── Tell-only API: animated ──────────────────────────────────────────────
    def show_letter_animated(self, letter: str, duration_ms: int) -> None:
        if duration_ms <= 0:
            self.show_letter(letter)
            return
        self._stop_active_anims()
        self.setText(letter.upper())
        self._border = TYPED_BORDER
        self._scale_value = TYPE_IN_INITIAL_SCALE
        self._opacity_value = 0.0
        self.update()

        scale_anim = QPropertyAnimation(self, b"scaleValue", self)
        scale_anim.setDuration(duration_ms)
        scale_anim.setStartValue(TYPE_IN_INITIAL_SCALE)
        scale_anim.setEndValue(1.0)
        scale_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        opacity_anim = QPropertyAnimation(self, b"opacityValue", self)
        opacity_anim.setDuration(duration_ms)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)

        group = QParallelAnimationGroup(self)
        group.addAnimation(scale_anim)
        group.addAnimation(opacity_anim)
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def clear_animated(
        self,
        duration_ms: int,
        on_done: Optional[Callable[[], None]] = None,
    ) -> None:
        if duration_ms <= 0:
            self.clear()
            if on_done is not None:
                on_done()
            return
        self._stop_active_anims()

        scale_anim = QPropertyAnimation(self, b"scaleValue", self)
        scale_anim.setDuration(duration_ms)
        scale_anim.setStartValue(self._scale_value)
        scale_anim.setEndValue(TYPE_IN_INITIAL_SCALE)
        scale_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        opacity_anim = QPropertyAnimation(self, b"opacityValue", self)
        opacity_anim.setDuration(duration_ms)
        opacity_anim.setStartValue(self._opacity_value)
        opacity_anim.setEndValue(0.0)

        group = QParallelAnimationGroup(self)
        group.addAnimation(scale_anim)
        group.addAnimation(opacity_anim)

        def finish() -> None:
            self.clear()
            if on_done is not None:
                on_done()

        group.finished.connect(finish)
        group.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def flip_reveal(
        self,
        result: LetterResult,
        duration_ms: int,
        on_done: Optional[Callable[[], None]] = None,
    ) -> None:
        if duration_ms <= 0:
            self.reveal(result)
            if on_done is not None:
                on_done()
            return
        self._stop_active_anims()

        half = max(1, duration_ms // 2)

        shrink = QPropertyAnimation(self, b"flipXValue", self)
        shrink.setDuration(half)
        shrink.setStartValue(1.0)
        shrink.setEndValue(0.0)
        shrink.setEasingCurve(QEasingCurve.Type.InCubic)

        def midpoint() -> None:
            self.reveal(result)
            expand = QPropertyAnimation(self, b"flipXValue", self)
            expand.setDuration(half)
            expand.setStartValue(0.0)
            expand.setEndValue(1.0)
            expand.setEasingCurve(QEasingCurve.Type.OutCubic)
            if on_done is not None:
                expand.finished.connect(on_done)
            expand.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        shrink.finished.connect(midpoint)
        shrink.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── Inspection (test-only) ───────────────────────────────────────────────
    @property
    def letter(self) -> str:
        return self.text()

    @property
    def background(self) -> str:
        return self._background

    @property
    def border(self) -> str:
        return self._border

    # ── Animation lifecycle ──────────────────────────────────────────────────
    def _stop_active_anims(self) -> None:
        for anim in self.findChildren(QAbstractAnimation):
            anim.stop()

    # ── Qt animation properties ──────────────────────────────────────────────
    def _get_scale(self) -> float:
        return self._scale_value

    def _set_scale(self, value: float) -> None:
        self._scale_value = value
        self.update()

    def _get_flip_x(self) -> float:
        return self._flip_x_value

    def _set_flip_x(self, value: float) -> None:
        self._flip_x_value = value
        self.update()

    def _get_opacity(self) -> float:
        return self._opacity_value

    def _set_opacity(self, value: float) -> None:
        self._opacity_value = value
        self.update()

    scaleValue = Property(float, _get_scale, _set_scale)
    flipXValue = Property(float, _get_flip_x, _set_flip_x)
    opacityValue = Property(float, _get_opacity, _set_opacity)

    # ── Custom paint ─────────────────────────────────────────────────────────
    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802 (Qt API)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity_value)

        cx = self.width() / 2
        cy = self.height() / 2
        painter.translate(cx, cy)
        painter.scale(
            self._scale_value * self._flip_x_value,
            self._scale_value,
        )
        painter.translate(-cx, -cy)

        rect = self.rect()
        painter.fillRect(rect, QColor(self._border))
        inner = rect.adjusted(
            TILE_BORDER_PX, TILE_BORDER_PX, -TILE_BORDER_PX, -TILE_BORDER_PX
        )
        painter.fillRect(inner, QColor(self._background))

        font = QFont(TILE_FONT_FAMILY, TILE_FONT_PX)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(self._text_color))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
