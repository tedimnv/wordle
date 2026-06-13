from __future__ import annotations

from enum import Enum

WORD_LENGTH = 5
MAX_GUESSES = 6


class LetterResult(Enum):
    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"
