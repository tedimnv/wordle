"""Integration tests against the real data/answers.txt and data/guesses.txt."""
import pytest
from pathlib import Path

from src.constants import WORD_LENGTH
from src.word_bank import WordBank

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_ANSWERS = PROJECT_ROOT / "data" / "answers.txt"
REAL_GUESSES = PROJECT_ROOT / "data" / "guesses.txt"

OFFICIAL_ANSWER_COUNT = 2315
OFFICIAL_ACCEPTED_COUNT = 12972


@pytest.fixture(scope="module")
def bank() -> WordBank:
    return WordBank(REAL_ANSWERS, REAL_GUESSES)


# ── File presence ────────────────────────────────────────────────────────────

def test_data_files_exist():
    assert REAL_ANSWERS.exists(), f"Missing {REAL_ANSWERS}"
    assert REAL_GUESSES.exists(), f"Missing {REAL_GUESSES}"


# ── Counts ───────────────────────────────────────────────────────────────────

def test_answer_count_matches_official(bank: WordBank):
    assert len(bank.answers) == OFFICIAL_ANSWER_COUNT


def test_accepted_total_matches_official(bank: WordBank):
    assert len(bank.accepted_guesses) == OFFICIAL_ACCEPTED_COUNT


# ── Word shape ───────────────────────────────────────────────────────────────

def test_all_answer_words_are_five_letters(bank: WordBank):
    assert all(len(w) == WORD_LENGTH for w in bank.answers)


def test_all_accepted_words_are_five_letters(bank: WordBank):
    assert all(len(w) == WORD_LENGTH for w in bank.accepted_guesses)


def test_all_answer_words_are_alpha_uppercase(bank: WordBank):
    assert all(w.isalpha() and w.isupper() for w in bank.answers)


def test_all_accepted_words_are_alpha_uppercase(bank: WordBank):
    assert all(w.isalpha() and w.isupper() for w in bank.accepted_guesses)


# ── Relationships & loader integrity ─────────────────────────────────────────

def test_answers_are_subset_of_accepted(bank: WordBank):
    assert bank.answers.issubset(bank.accepted_guesses)


def _expected_from_file(path: Path) -> set[str]:
    return {
        word
        for raw in path.read_text().splitlines()
        if (word := raw.strip().upper()) and len(word) == WORD_LENGTH and word.isalpha()
    }


def test_no_silent_dropping_in_answers_file():
    loaded = WordBank(REAL_ANSWERS).answers
    assert loaded == _expected_from_file(REAL_ANSWERS)


def test_no_silent_dropping_in_guesses_file(bank: WordBank):
    assert _expected_from_file(REAL_GUESSES).issubset(bank.accepted_guesses)


# ── Spot checks ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("word", ["CRANE", "ABOUT", "PROUD", "SLATE", "AUDIO"])
def test_common_words_are_valid_answers(bank: WordBank, word: str):
    assert word in bank.answers
    assert bank.is_valid(word) is True


@pytest.mark.parametrize("word", ["AALII", "AAHED", "ZYMIC"])
def test_obscure_words_are_accepted_but_not_answers(bank: WordBank, word: str):
    assert bank.is_valid(word) is True
    assert word not in bank.answers


@pytest.mark.parametrize("word", ["ZZZZZ", "XXXXX", "QWXYZ"])
def test_nonsense_words_are_rejected(bank: WordBank, word: str):
    assert bank.is_valid(word) is False


# ── Randomness ───────────────────────────────────────────────────────────────

def test_get_answer_always_from_answer_pool(bank: WordBank):
    for _ in range(100):
        assert bank.get_answer() in bank.answers


def test_get_answer_produces_variety(bank: WordBank):
    results = {bank.get_answer() for _ in range(100)}
    assert len(results) > 50


# ── Letter coverage ──────────────────────────────────────────────────────────

def test_answer_letter_coverage(bank: WordBank):
    """Answers span every starting letter except X (matches official list)."""
    assert {w[0] for w in bank.answers} == set("ABCDEFGHIJKLMNOPQRSTUVWYZ")


def test_accepted_letter_coverage_is_full_alphabet(bank: WordBank):
    assert {w[0] for w in bank.accepted_guesses} == set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
