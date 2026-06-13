from __future__ import annotations

from src.constants import LetterResult, WORD_LENGTH


class Evaluator:
    @staticmethod
    def evaluate(guess: str, answer: str) -> list[LetterResult]:
        Evaluator._validate(guess, "guess")
        Evaluator._validate(answer, "answer")

        guess = guess.upper()
        remaining = list(answer.upper())
        results = [LetterResult.ABSENT] * WORD_LENGTH

        Evaluator._mark_correct(guess, results, remaining)
        Evaluator._mark_present(guess, results, remaining)
        return results

    @staticmethod
    def _mark_correct(
        guess: str,
        results: list[LetterResult],
        remaining: list[str | None],
    ) -> None:
        for i in range(WORD_LENGTH):
            if guess[i] == remaining[i]:
                results[i] = LetterResult.CORRECT
                remaining[i] = None

    @staticmethod
    def _mark_present(
        guess: str,
        results: list[LetterResult],
        remaining: list[str | None],
    ) -> None:
        for i in range(WORD_LENGTH):
            if results[i] == LetterResult.CORRECT:
                continue
            if guess[i] in remaining:
                results[i] = LetterResult.PRESENT
                remaining[remaining.index(guess[i])] = None

    @staticmethod
    def _validate(word: str, label: str) -> None:
        if len(word) != WORD_LENGTH:
            raise ValueError(
                f"{label} must be {WORD_LENGTH} characters, got {len(word)}"
            )
        if not word.isalpha():
            raise ValueError(f"{label} must contain only letters")
