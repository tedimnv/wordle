from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout, QWidget

from src.constants import LetterResult, MAX_GUESSES, WORD_LENGTH
from src.theme import TILE_GAP_PX
from src.tile import Tile


class Board(QWidget):
    """6×5 Wordle tile grid. Pure presentation — no game logic."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tiles: list[list[Tile]] = []
        self._reveal_timers: list[QTimer] = []
        self._build()

    # ── Tell-only API ────────────────────────────────────────────────────────
    def set_letter(self, row: int, col: int, letter: str) -> None:
        tile = self._tile_at(row, col)
        if tile is not None:
            tile.show_letter(letter)

    def set_letter_animated(
        self, row: int, col: int, letter: str, duration_ms: int
    ) -> None:
        tile = self._tile_at(row, col)
        if tile is not None:
            tile.show_letter_animated(letter, duration_ms)

    def clear_letter(self, row: int, col: int) -> None:
        tile = self._tile_at(row, col)
        if tile is not None:
            tile.clear()

    def clear_letter_animated(self, row: int, col: int, duration_ms: int) -> None:
        tile = self._tile_at(row, col)
        if tile is not None:
            tile.clear_animated(duration_ms)

    def reveal_row(self, row: int, results: list[LetterResult]) -> None:
        if not self._row_in_range(row):
            return
        if len(results) != WORD_LENGTH:
            raise ValueError(f"reveal_row expects {WORD_LENGTH} results")
        for c, result in enumerate(results):
            self._tiles[row][c].reveal(result)

    def reveal_row_animated(
        self,
        row: int,
        results: list[LetterResult],
        step_ms: int,
        on_done: Optional[Callable[[], None]] = None,
        flip_ms: int = 400,
    ) -> None:
        if not self._row_in_range(row):
            return
        if len(results) != WORD_LENGTH:
            raise ValueError(f"reveal_row_animated expects {WORD_LENGTH} results")
        if step_ms <= 0:
            self.reveal_row(row, results)
            if on_done is not None:
                on_done()
            return
        last = WORD_LENGTH - 1
        for col in range(WORD_LENGTH):
            done_cb = on_done if col == last else None
            self._schedule_flip(row, col, results[col], col * step_ms, flip_ms, done_cb)

    def _schedule_flip(
        self,
        row: int,
        col: int,
        result: LetterResult,
        delay_ms: int,
        flip_ms: int,
        on_done: Optional[Callable[[], None]],
    ) -> None:
        if delay_ms == 0:
            self._tiles[row][col].flip_reveal(result, flip_ms, on_done=on_done)
            return
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(
            lambda: self._tiles[row][col].flip_reveal(result, flip_ms, on_done=on_done)
        )
        timer.start(delay_ms)
        self._reveal_timers.append(timer)

    def reset(self) -> None:
        for timer in self._reveal_timers:
            timer.stop()
        self._reveal_timers.clear()
        for row in self._tiles:
            for tile in row:
                tile.clear()

    # ── Inspection (test-only) ───────────────────────────────────────────────
    def get_letter(self, row: int, col: int) -> str:
        tile = self._tile_at(row, col)
        return tile.letter if tile is not None else ""

    def get_background(self, row: int, col: int) -> str:
        tile = self._tile_at(row, col)
        return tile.background if tile is not None else ""

    def get_border(self, row: int, col: int) -> str:
        tile = self._tile_at(row, col)
        return tile.border if tile is not None else ""

    # ── Internal ─────────────────────────────────────────────────────────────
    def _build(self) -> None:
        layout = QGridLayout(self)
        layout.setSpacing(TILE_GAP_PX)
        layout.setContentsMargins(0, 0, 0, 0)
        for r in range(MAX_GUESSES):
            row: list[Tile] = []
            for c in range(WORD_LENGTH):
                tile = Tile(self)
                layout.addWidget(tile, r, c)
                row.append(tile)
            self._tiles.append(row)

    def _tile_at(self, row: int, col: int) -> Tile | None:
        if not self._row_in_range(row) or not (0 <= col < WORD_LENGTH):
            return None
        return self._tiles[row][col]

    @staticmethod
    def _row_in_range(row: int) -> bool:
        return 0 <= row < MAX_GUESSES
