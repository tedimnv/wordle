from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from src.constants import LetterResult
from src.styles import key_style
from src.theme import (
    KEY_BG,
    KEY_GAP_PX,
    KEY_HEIGHT_PX,
    KEY_ROW_SPACING_PX,
    KEY_TEXT,
    KEY_WIDE_WIDTH_PX,
    KEY_WIDTH_PX,
    RESULT_BG,
    REVEALED_TEXT,
)

TOP_ROW = "QWERTYUIOP"
MIDDLE_ROW = "ASDFGHJKL"
BOTTOM_ROW = "ZXCVBNM"
ENTER_LABEL = "ENTER"
BACKSPACE_LABEL = "⌫"

_PRIORITY: dict[Optional[LetterResult], int] = {
    None: 0,
    LetterResult.ABSENT: 1,
    LetterResult.PRESENT: 2,
    LetterResult.CORRECT: 3,
}


def _noop_letter(_letter: str) -> None: ...
def _noop() -> None: ...


class Keyboard(QWidget):
    """On-screen QWERTY keyboard. Pure presentation + click dispatch."""

    def __init__(
        self,
        parent: QWidget | None = None,
        on_letter: Optional[Callable[[str], None]] = None,
        on_enter: Optional[Callable[[], None]] = None,
        on_backspace: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._on_letter = on_letter or _noop_letter
        self._on_enter = on_enter or _noop
        self._on_backspace = on_backspace or _noop

        self._letter_buttons: dict[str, QPushButton] = {}
        self._states: dict[str, Optional[LetterResult]] = {}
        self._enter_button: QPushButton | None = None
        self._backspace_button: QPushButton | None = None

        self._build()

    # ── Tell-only API ────────────────────────────────────────────────────────
    def update_key(self, letter: str, result: LetterResult) -> None:
        letter = letter.upper()
        if letter not in self._letter_buttons:
            return
        if _PRIORITY[result] <= _PRIORITY[self._states[letter]]:
            return
        self._states[letter] = result
        self._letter_buttons[letter].setStyleSheet(
            key_style(RESULT_BG[result], REVEALED_TEXT)
        )

    def reset(self) -> None:
        default = key_style(KEY_BG, KEY_TEXT)
        for letter, btn in self._letter_buttons.items():
            btn.setStyleSheet(default)
            self._states[letter] = None

    # ── Inspection / test-only ───────────────────────────────────────────────
    def get_key_background(self, letter: str) -> str:
        upper = letter.upper()
        if upper not in self._letter_buttons:
            return ""
        state = self._states[upper]
        return KEY_BG if state is None else RESULT_BG[state]

    def has_letter_key(self, letter: str) -> bool:
        return letter.upper() in self._letter_buttons

    def click_key(self, letter: str) -> None:
        btn = self._letter_buttons.get(letter.upper())
        if btn is not None:
            btn.click()

    def click_enter(self) -> None:
        assert self._enter_button is not None
        self._enter_button.click()

    def click_backspace(self) -> None:
        assert self._backspace_button is not None
        self._backspace_button.click()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setSpacing(KEY_ROW_SPACING_PX)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._letter_row(TOP_ROW))
        outer.addWidget(self._letter_row(MIDDLE_ROW))
        outer.addWidget(self._bottom_row(BOTTOM_ROW))

    def _letter_row(self, letters: str) -> QWidget:
        row, layout = self._row_skeleton()
        for letter in letters:
            self._add_letter_key(row, layout, letter)
        return row

    def _bottom_row(self, letters: str) -> QWidget:
        row, layout = self._row_skeleton()
        self._enter_button = self._make_button(row, ENTER_LABEL, self._on_enter, wide=True)
        layout.addWidget(self._enter_button)
        for letter in letters:
            self._add_letter_key(row, layout, letter)
        self._backspace_button = self._make_button(
            row, BACKSPACE_LABEL, self._on_backspace, wide=True
        )
        layout.addWidget(self._backspace_button)
        return row

    def _row_skeleton(self) -> tuple[QWidget, QHBoxLayout]:
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setSpacing(KEY_GAP_PX)
        layout.setContentsMargins(0, 0, 0, 0)
        return row, layout

    def _add_letter_key(self, parent: QWidget, layout: QHBoxLayout, letter: str) -> None:
        btn = self._make_button(parent, letter, self._letter_handler(letter))
        self._letter_buttons[letter] = btn
        self._states[letter] = None
        layout.addWidget(btn)

    def _letter_handler(self, letter: str) -> Callable[[], None]:
        def handler() -> None:
            self._on_letter(letter)
        return handler

    @staticmethod
    def _make_button(
        parent: QWidget,
        text: str,
        command: Callable[[], None],
        wide: bool = False,
    ) -> QPushButton:
        btn = QPushButton(text, parent)
        btn.setFixedSize(
            KEY_WIDE_WIDTH_PX if wide else KEY_WIDTH_PX,
            KEY_HEIGHT_PX,
        )
        btn.setStyleSheet(key_style(KEY_BG, KEY_TEXT))
        btn.clicked.connect(command)
        return btn
