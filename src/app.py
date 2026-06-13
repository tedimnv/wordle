from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.board import Board
from src.constants import LetterResult, WORD_LENGTH
from src.evaluator import Evaluator
from src.keyboard import Keyboard
from src.state_machine import StateMachine
from src.styles import action_button_style
from src.theme import EMPTY_BG, EMPTY_TEXT
from src.word_bank import WordBank

DEFAULT_REVEAL_STEP_MS = 300
TYPE_IN_MS = 120

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANSWERS = PROJECT_ROOT / "data" / "answers.txt"
DEFAULT_GUESSES = PROJECT_ROOT / "data" / "guesses.txt"

MSG_TOO_SHORT = "Not enough letters"
MSG_INVALID = "Not in word list"
MSG_WIN = "You won!"


def _default_word_bank() -> WordBank:
    return WordBank(DEFAULT_ANSWERS, DEFAULT_GUESSES)


class App(QMainWindow):
    """Main window — wires WordBank, StateMachine, Evaluator, Board, Keyboard."""

    def __init__(
        self,
        word_bank: Optional[WordBank] = None,
        reveal_step_ms: int = DEFAULT_REVEAL_STEP_MS,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Wordle")

        self._word_bank = word_bank if word_bank is not None else _default_word_bank()
        self._state = StateMachine()
        self._reveal_step_ms = reveal_step_ms
        self._answer = ""
        self._typed: list[str] = []
        self._revealing = False

        self._board = Board()
        self._keyboard = Keyboard(
            on_letter=self.type_letter,
            on_enter=self.submit,
            on_backspace=self.backspace,
        )
        self._message_label = QLabel("")
        self._new_game_button = QPushButton("New Game")
        self._new_game_button.setStyleSheet(action_button_style())
        self._new_game_button.clicked.connect(self.new_game)

        self._build_layout()
        self.new_game()

    # ── Public actions ───────────────────────────────────────────────────────
    def type_letter(self, letter: str) -> None:
        if not self._accepting_input() or len(self._typed) >= WORD_LENGTH:
            return
        letter = letter.upper()
        if not (len(letter) == 1 and letter.isalpha()):
            return
        col = len(self._typed)
        self._typed.append(letter)
        if self._reveal_step_ms > 0:
            self._board.set_letter_animated(
                self._state.current_row, col, letter, TYPE_IN_MS
            )
        else:
            self._board.set_letter(self._state.current_row, col, letter)
        self._clear_message()

    def backspace(self) -> None:
        if not self._accepting_input() or not self._typed:
            return
        self._typed.pop()
        col = len(self._typed)
        if self._reveal_step_ms > 0:
            self._board.clear_letter_animated(
                self._state.current_row, col, TYPE_IN_MS
            )
        else:
            self._board.clear_letter(self._state.current_row, col)
        self._clear_message()

    def submit(self) -> None:
        if not self._accepting_input():
            return
        if len(self._typed) < WORD_LENGTH:
            self._show_message(MSG_TOO_SHORT)
            return
        word = "".join(self._typed)
        if not self._word_bank.is_valid(word):
            self._show_message(MSG_INVALID)
            return
        self._evaluate_and_apply(word)

    def _accepting_input(self) -> bool:
        return self._state.is_active and not self._revealing

    def new_game(self) -> None:
        self._state.reset()
        self._board.reset()
        self._keyboard.reset()
        self._typed = []
        self._revealing = False
        self._answer = self._word_bank.get_answer()
        self._clear_message()
        self._state.start_game()

    # ── Inspection (test-only) ───────────────────────────────────────────────
    @property
    def board(self) -> Board:
        return self._board

    @property
    def keyboard(self) -> Keyboard:
        return self._keyboard

    @property
    def state(self) -> StateMachine:
        return self._state

    @property
    def answer(self) -> str:
        return self._answer

    @property
    def message(self) -> str:
        return self._message_label.text()

    # ── Physical key handling ────────────────────────────────────────────────
    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt API)
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.submit()
        elif key == Qt.Key.Key_Backspace:
            self.backspace()
        else:
            text = event.text()
            if len(text) == 1 and text.isalpha():
                self.type_letter(text)
        super().keyPressEvent(event)

    # ── Internals ────────────────────────────────────────────────────────────
    def _evaluate_and_apply(self, word: str) -> None:
        results = Evaluator.evaluate(word, self._answer)
        row = self._state.current_row
        self._state.submit_guess(results)
        self._typed = []
        self._revealing = True
        self._board.reveal_row_animated(
            row,
            results,
            step_ms=self._reveal_step_ms,
            on_done=lambda: self._after_reveal(word, results),
        )

    def _after_reveal(self, word: str, results: list[LetterResult]) -> None:
        for letter, result in zip(word, results):
            self._keyboard.update_key(letter, result)
        self._revealing = False
        if self._state.is_won:
            self._show_message(MSG_WIN)
        elif self._state.is_lost:
            self._show_message(f"Word was {self._answer}")

    def _show_message(self, text: str) -> None:
        self._message_label.setText(text)

    def _clear_message(self) -> None:
        self._message_label.setText("")

    def _build_layout(self) -> None:
        central = QWidget(self)
        central.setStyleSheet(f"background-color: {EMPTY_BG};")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("WORDLE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Helvetica Neue", 32, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {EMPTY_TEXT};")

        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message_label.setFont(QFont("Helvetica Neue", 13, QFont.Weight.Bold))
        self._message_label.setStyleSheet(f"color: {EMPTY_TEXT};")
        self._message_label.setMinimumHeight(20)

        layout.addWidget(title)
        layout.addWidget(self._board, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._message_label)
        layout.addWidget(self._keyboard, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._new_game_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setCentralWidget(central)


def main() -> None:  # pragma: no cover
    import sys
    from PySide6.QtWidgets import QApplication

    qt_app = QApplication.instance() or QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(qt_app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
