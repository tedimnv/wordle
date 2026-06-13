from __future__ import annotations

import random
from pathlib import Path

from src.constants import WORD_LENGTH


class WordBank:
    """
    Two-list word bank, modelled after the original Wordle.

    - `answers` is the pool the computer picks from.
    - `accepted_guesses` is the full set the user may type (answers ∪ extras).
    """

    def __init__(
        self,
        answers_path: str | Path,
        guesses_path: str | Path | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self._answers = self._load(Path(answers_path))
        extras = self._load(Path(guesses_path)) if guesses_path is not None else set()
        self._accepted = self._answers | extras
        self._rng = rng if rng is not None else random.Random()

    # ── Public API ───────────────────────────────────────────────────────────
    def get_answer(self) -> str:
        return self._rng.choice(sorted(self._answers))

    def is_valid(self, word: object) -> bool:
        if not isinstance(word, str):
            return False
        if len(word) != WORD_LENGTH or not word.isalpha():
            return False
        return word.upper() in self._accepted

    @property
    def answers(self) -> set[str]:
        return self._answers

    @property
    def accepted_guesses(self) -> set[str]:
        return self._accepted

    # ── Internals ────────────────────────────────────────────────────────────
    @staticmethod
    def _load(path: Path) -> set[str]:
        if not path.exists():
            raise FileNotFoundError(f"Word file not found: {path}")
        return {
            word
            for raw in path.read_text().splitlines()
            if (word := raw.strip().upper())
            and len(word) == WORD_LENGTH
            and word.isalpha()
        }
