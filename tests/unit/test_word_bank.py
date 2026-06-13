"""Unit tests for WordBank — synthetic fixtures only.

Tests against the real data/answers.txt and data/guesses.txt live in
test_word_bank_real.py.
"""
import random
import pytest
from pathlib import Path

from src.constants import WORD_LENGTH
from src.word_bank import WordBank


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def answers_file(tmp_path: Path) -> Path:
    p = tmp_path / "answers.txt"
    p.write_text("crane\nslate\nproud\nfaint\nabout\n")
    return p


@pytest.fixture
def guesses_file(tmp_path: Path) -> Path:
    p = tmp_path / "guesses.txt"
    p.write_text("aalii\nzayin\naback\n")
    return p


@pytest.fixture
def messy_file(tmp_path: Path) -> Path:
    """File with blank lines, whitespace, and a non-5-letter word."""
    p = tmp_path / "messy.txt"
    p.write_text("  crane  \n\n\nslate\n   \nabout\nhi\nelephant\n")
    return p


# ── Word loading ──────────────────────────────────────────────────────────────

def test_loads_answers_from_file(answers_file: Path):
    bank = WordBank(answers_file)
    assert bank.answers == {"CRANE", "SLATE", "PROUD", "FAINT", "ABOUT"}


def test_all_loaded_words_are_five_letters(answers_file: Path):
    bank = WordBank(answers_file)
    assert all(len(w) == WORD_LENGTH for w in bank.answers)


def test_missing_answers_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        WordBank(tmp_path / "does_not_exist.txt")


def test_missing_guesses_file_raises(answers_file: Path, tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        WordBank(answers_file, tmp_path / "missing.txt")


def test_ignores_blank_lines_and_whitespace(messy_file: Path):
    bank = WordBank(messy_file)
    assert bank.answers == {"CRANE", "SLATE", "ABOUT"}


def test_ignores_non_five_letter_words(messy_file: Path):
    bank = WordBank(messy_file)
    assert "HI" not in bank.answers
    assert "ELEPHANT" not in bank.answers


def test_accepts_path_as_string(answers_file: Path):
    bank = WordBank(str(answers_file))
    assert "CRANE" in bank.answers


# ── Two-list behavior ────────────────────────────────────────────────────────

def test_accepted_guesses_is_union(answers_file: Path, guesses_file: Path):
    bank = WordBank(answers_file, guesses_file)
    assert bank.accepted_guesses == {
        "CRANE", "SLATE", "PROUD", "FAINT", "ABOUT",
        "AALII", "ZAYIN", "ABACK",
    }


def test_get_answer_only_picks_from_answers(answers_file: Path, guesses_file: Path):
    bank = WordBank(answers_file, guesses_file)
    for _ in range(50):
        assert bank.get_answer() in bank.answers


def test_extra_guess_is_valid_but_not_in_answers(answers_file: Path, guesses_file: Path):
    bank = WordBank(answers_file, guesses_file)
    assert bank.is_valid("AALII") is True
    assert "AALII" not in bank.answers


def test_without_guesses_file_only_answers_are_accepted(answers_file: Path):
    bank = WordBank(answers_file)
    assert bank.accepted_guesses == bank.answers


# ── get_answer() ──────────────────────────────────────────────────────────────

def test_get_answer_returns_word_from_answers(answers_file: Path):
    bank = WordBank(answers_file)
    assert bank.get_answer() in bank.answers


def test_get_answer_is_not_always_the_same(answers_file: Path):
    bank = WordBank(answers_file)
    results = {bank.get_answer() for _ in range(20)}
    assert len(results) > 1


def test_seeded_random_is_deterministic(answers_file: Path):
    bank_a = WordBank(answers_file, rng=random.Random(42))
    bank_b = WordBank(answers_file, rng=random.Random(42))
    assert (
        [bank_a.get_answer() for _ in range(10)]
        == [bank_b.get_answer() for _ in range(10)]
    )


# ── is_valid() ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("word,expected", [
    ("CRANE",   True),
    ("crane",   True),
    ("CrAnE",   True),
    ("ZZZZZ",   False),
    ("CRAN",    False),
    ("CRANES",  False),
    ("",        False),
    ("CRAN3",   False),
    ("CR NE",   False),
])
def test_is_valid_string_inputs(answers_file: Path, word: str, expected: bool):
    bank = WordBank(answers_file)
    assert bank.is_valid(word) is expected


def test_is_valid_false_for_non_string(answers_file: Path):
    bank = WordBank(answers_file)
    assert bank.is_valid(12345) is False  # type: ignore[arg-type]
