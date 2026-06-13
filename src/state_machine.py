from __future__ import annotations

from enum import Enum

from src.constants import LetterResult, MAX_GUESSES, WORD_LENGTH


class GameState(Enum):
    IDLE = "idle"
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


class InvalidStateError(Exception):
    pass


class StateMachine:
    def __init__(self) -> None:
        self._state = GameState.IDLE
        self._current_row = 0
        self._guesses: list[list[LetterResult]] = []

    # ── Read-only views ──────────────────────────────────────────────────────
    @property
    def state(self) -> GameState:
        return self._state

    @property
    def current_row(self) -> int:
        return self._current_row

    @property
    def guesses(self) -> list[list[LetterResult]]:
        return [list(g) for g in self._guesses]

    # ── Tell-don't-ask predicates ────────────────────────────────────────────
    @property
    def is_active(self) -> bool:
        return self._state == GameState.PLAYING

    @property
    def is_finished(self) -> bool:
        return self._state in (GameState.WON, GameState.LOST)

    @property
    def is_won(self) -> bool:
        return self._state == GameState.WON

    @property
    def is_lost(self) -> bool:
        return self._state == GameState.LOST

    # ── Transitions ──────────────────────────────────────────────────────────
    def start_game(self) -> None:
        self._require_state(GameState.IDLE, "start_game")
        self._state = GameState.PLAYING

    def submit_guess(self, result: list[LetterResult]) -> None:
        self._require_state(GameState.PLAYING, "submit_guess")
        self._validate_result(result)
        self._record(result)
        self._transition_after_guess(result)

    def reset(self) -> None:
        self._state = GameState.IDLE
        self._current_row = 0
        self._guesses = []

    # ── Internals ────────────────────────────────────────────────────────────
    def _require_state(self, expected: GameState, action: str) -> None:
        if self._state != expected:
            raise InvalidStateError(
                f"{action}() requires {expected.value}, current state is {self._state.value}"
            )

    @staticmethod
    def _validate_result(result: list[LetterResult]) -> None:
        if not isinstance(result, list) or len(result) != WORD_LENGTH:
            raise ValueError(f"result must be a list of {WORD_LENGTH} items")

    def _record(self, result: list[LetterResult]) -> None:
        self._guesses.append(list(result))
        self._current_row += 1

    def _transition_after_guess(self, result: list[LetterResult]) -> None:
        if all(r == LetterResult.CORRECT for r in result):
            self._state = GameState.WON
        elif self._current_row >= MAX_GUESSES:
            self._state = GameState.LOST
