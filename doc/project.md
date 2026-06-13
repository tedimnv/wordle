# Wordle — Decisions

## Language & Runtime
- Python application

## Interface
- GUI application (not terminal)
- Both keyboard and mouse must work for all interactions
- **GUI framework: PySide6** (Qt for Python). Chosen over tkinter for a modern native look and better layout primitives. Logic layer (StateMachine, Evaluator, WordBank) is framework-agnostic.
- **UI tests use `pytest-qt`** — the `qtbot` fixture manages the `QApplication` lifecycle and provides widget-cleanup helpers.

## Visuals
- Tiles are colored based on guess result:
  - Green — correct letter, correct position
  - Yellow — correct letter, wrong position
  - Grey — letter not in the word

## Rules (standard Wordle)
- 5-letter words only
- 6 attempts to guess the word
- After each guess, tiles reveal their colors
- Game ends on correct guess or after 6 failed attempts

## Scope
- Full game from start to finish: title, gameplay, win/lose state, ability to play again

## Coding style
- Every module starts with `from __future__ import annotations` (PEP 563-style deferred annotations)
- Shared constants live in `src/constants.py` — never duplicate them
- Result codes are `LetterResult` enum values, not magic strings
- Public API: read-only state via `@property`; mutation via verbs (`start_game`, `submit_guess`, `reset`)
- Tell-don't-ask: components expose boolean predicates (`is_won`, `is_finished`, …) so callers
  don't switch on raw enum values
- Methods stay short — split high-complexity methods into single-purpose helpers
- No comments that describe what the code does; comments only when the *why* is non-obvious

---

## Architecture — Component Design

### Shared types — `src/constants.py`
A single source of truth for cross-component primitives:
- `WORD_LENGTH = 5`, `MAX_GUESSES = 6`
- `LetterResult` enum (`CORRECT` / `PRESENT` / `ABSENT`)

Why: previously these were duplicated as magic strings and bare integers across the Evaluator and
StateMachine. The enum gives type safety, eliminates typo risk, and removes hidden coupling between
modules.

### Visual theme — `src/theme.py` and `src/styles.py`
- `theme.py`: pure data — hex colors, font family/size, geometry constants.
- `styles.py`: stylesheet builders (`tile_style`, `key_style`). UI widgets never concatenate
  CSS-like strings themselves.

The game is split into independent, testable components:

### StateMachine
Owns the game lifecycle. Transitions between states:
- `IDLE` → `PLAYING` (new game started)
- `PLAYING` → `PLAYING` (guess submitted, not yet won/lost)
- `PLAYING` → `WON` (correct guess)
- `PLAYING` → `LOST` (6 guesses used, no correct guess)
- `WON` / `LOST` → `IDLE` (new game)

Exposes **tell-don't-ask** predicates so callers don't have to inspect the raw state enum:
`is_active`, `is_finished`, `is_won`, `is_lost`.

`submit_guess` is composed from four single-purpose helpers (`_require_state`, `_validate_result`,
`_record`, `_transition_after_guess`) to keep cyclomatic complexity low.

No UI knowledge. Pure logic, fully unit-testable.

### Evaluator (algorithm component)
Takes a guess string and the answer string, returns per-letter `LetterResult` values: `CORRECT`, `PRESENT`, or `ABSENT`.
Handles the duplicate-letter edge case correctly (same rules as the original Wordle).
Stateless. Split internally into `_mark_correct` (first pass) and `_mark_present` (second pass) for low cyclomatic complexity.
Fully unit-testable.

### WordBank
Manages **two** word lists, modelled after the original Wordle:
- `data/answers.txt` — pool the computer picks the daily answer from (curated, common words)
- `data/guesses.txt` — extra accepted guesses (obscure but real 5-letter words)

API:
- `get_answer()` — picks from answers only
- `is_valid(word)` — accepts answers ∪ guesses (case-insensitive)
- `accepted_guesses` — the full set the user is allowed to type

This means the user can guess obscure-but-real words to probe letters, but the answer is always something recognizable. Fully unit-testable.

### Tile (UI component)
A single 62×62 `QLabel` that knows its own visual state. Three transitions:
`show_letter` (typed), `clear` (empty), `reveal` (colored). No board awareness.
Lives in `src/tile.py`.

### Board (UI component)
A 6×5 `QGridLayout` of `Tile` widgets. Tells individual tiles what to do; never reaches
into their internals. Out-of-bounds access is a silent no-op for tells, an empty string
for queries. Lives in `src/board.py`.

### Keyboard (UI component)
A 3-row QWERTY on-screen keyboard. Build is split into focused helpers
(`_letter_row`, `_bottom_row`, `_row_skeleton`, `_add_letter_key`) to keep cyclomatic
complexity low. Keys track best-known state and don't downgrade. Accepts both click and
physical key events (physical wiring happens in App). Lives in `src/keyboard.py`.

### Styles (presentation helper)
`src/styles.py` centralizes the Qt stylesheet strings used by tiles and keys. No UI
component builds raw style strings inline — they call `tile_style()` or `key_style()`.

### App (entry point / wiring)
Creates the window, instantiates all components, wires them together.
Not independently testable — covered by integration tests.

---

## Testing Strategy

### Test runner
- `pytest`

### Unit tests — pure logic, no GUI
| Component | File | What to test |
|-----------|------|-------------|
| Evaluator | `test_evaluator.py` | Correct/present/absent classification, duplicate letter edge cases |
| StateMachine | `test_state_machine.py` | All valid transitions, invalid transition guards, TDA predicates |
| WordBank (logic) | `test_word_bank.py` | Random word is valid, word validation, two-list union behavior — synthetic fixtures |
| WordBank (data) | `test_word_bank_real.py` | Real `data/answers.txt` + `data/guesses.txt` integrity — sizes, no silent drops, spot checks |

### UI tests — tkinter with event simulation
| Component | What to test |
|-----------|-------------|
| Board | Tile updates letter and color on guess submission |
| Keyboard | Key color updates after a guess; click fires correct letter |
| Integration | Type a full guess via keyboard → tiles update → colors revealed |

UI tests use `tkinter`'s `event_generate` to simulate keyboard presses and button clicks without a human. The window is created in the test, driven programmatically, then destroyed.
