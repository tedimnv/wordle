# Wordle — Plan

## Coverage Criteria

| Layer | Line coverage | Branch coverage |
|-------|--------------|----------------|
| Pure logic (Evaluator, StateMachine, WordBank) | 100% | 100% |
| UI components (Board, Keyboard) | 90%+ | 80%+ |
| App wiring | covered by integration tests |

Every public method must have at least one test. Every branch (if/else, early return) must be exercised. All known edge cases are listed explicitly per step.

---

## [x] Phase 1 — Foundation

### [x] Step 1 — Project structure & test infrastructure

Create the directory layout and configure the test runner before writing any game code.

```
Wordle/
├── CLAUDE.md
├── doc/
│   ├── plan.md
│   └── project.md
├── src/
│   ├── __init__.py
│   ├── evaluator.py
│   ├── word_bank.py
│   ├── state_machine.py
│   ├── board.py
│   ├── keyboard.py
│   └── app.py
├── tests/
│   ├── __init__.py
│   ├── test_smoke.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_evaluator.py
│   │   ├── test_word_bank.py
│   │   └── test_state_machine.py
│   └── ui/
│       ├── __init__.py
│       ├── test_board.py
│       ├── test_keyboard.py
│       └── test_integration.py
├── words.txt           ← full word list
├── pyproject.toml
└── pytest.ini
```

**pytest.ini** — configure coverage thresholds, mark slow UI tests so they can be skipped.

**Done when:** all imports resolve, smoke test passes with exit code 0.

---

## [x] Phase 2 — Core Logic

### [x] Step 1 — Evaluator

The core algorithm. Takes `guess: str` and `answer: str`, returns a list of 5 results, each one of `"correct"` / `"present"` / `"absent"`.

#### Algorithm rules
1. First pass — mark exact matches (`correct`). Remove matched positions from further consideration.
2. Second pass — for remaining letters, mark `present` if the letter exists in the remaining answer letters (consuming each answer letter at most once). Otherwise `absent`.

#### Unit tests — `tests/unit/test_evaluator.py`

**Happy path**
- All correct: `CRANE` vs `CRANE` → `[correct, correct, correct, correct, correct]`
- All absent: `ZZZZZ` vs `CRANE` → `[absent, absent, absent, absent, absent]`
- Mix of all three: `CRANE` vs `CRATE` → `[correct, correct, correct, absent, present]`

**Duplicate letter edge cases** — this is where most Wordle implementations break
- Letter appears once in answer, twice in guess — only one should be marked non-absent:
  `SPEED` vs `SPREE` → S=correct, P=correct, E=present, E=correct, D=absent
  `AABBB` vs `ABBAA` → A=correct, A=present, B=present, B=correct, B=absent
  `ABBEY` vs `KEBAB` → A=absent, B=present, B=correct, E=present, Y=absent
- Letter appears twice in answer, once in guess:
  `CRANE` vs `ERROR` → C=absent, R=present, A=absent, N=absent, E=absent
- Letter appears twice in answer, twice in guess:
  `SPEED` vs `STEED` → S=correct, P=absent, E=present, E=correct, D=correct

**Input guards**
- Guess or answer not exactly 5 characters → raise `ValueError`
- Non-alphabetic characters in guess or answer → raise `ValueError`
- Comparison is case-insensitive (mixed case input gives same result as uppercase)

**Done when:** all tests pass, 100% line and branch coverage on `evaluator.py`.

---

### [x] Step 2 — WordBank

Owns the word list. Two responsibilities: pick a random answer, validate a guess.

#### Unit tests — `tests/unit/test_word_bank.py`

**Word loading**
- Loads words from file correctly; all loaded words are exactly 5 letters
- Raises `FileNotFoundError` if word file is missing
- Ignores blank lines and whitespace in the file

**Random word**
- `get_answer()` returns a word that is in the word list
- Calling it repeatedly does not always return the same word (probabilistic — run 20 times, assert not all identical)
- Seeded random gives deterministic result

**Validation**
- `is_valid(word)` returns `True` for a known word (case-insensitive)
- `is_valid(word)` returns `False` for a real word not in the list (e.g. `"ZZZZZ"`)
- `is_valid(word)` returns `False` for a non-5-letter string
- `is_valid(word)` returns `False` for empty string
- `is_valid(word)` returns `False` for a string with non-alpha characters
- `is_valid(word)` is case-insensitive: `"crane"` and `"CRANE"` both return `True`

**Done when:** all tests pass, 100% line and branch coverage on `word_bank.py`.

---

### [x] Step 3 — StateMachine

Owns the game lifecycle. No UI, no word logic — only state and transitions.

#### States
`IDLE` → `PLAYING` → `WON`
`IDLE` → `PLAYING` → `LOST`
`WON`  → `IDLE`
`LOST` → `IDLE`

#### Unit tests — `tests/unit/test_state_machine.py`

**Initial state**
- Starts in `IDLE`
- `current_row` is 0, `guesses` list is empty

**Transitions — valid**
- `start_game()` from `IDLE` → moves to `PLAYING`
- `submit_guess(result)` with non-winning result from `PLAYING` → stays `PLAYING`, increments row
- `submit_guess(result)` with all-correct result → moves to `WON`
- `submit_guess(result)` with non-winning result on row 6 → moves to `LOST`
- `reset()` from `WON` → returns to `IDLE`, row resets to 0, guesses cleared
- `reset()` from `LOST` → same as above

**Transitions — invalid (must raise consistently)**
- `submit_guess()` when in `IDLE` → raises `InvalidStateError`
- `submit_guess()` when in `WON` → raises `InvalidStateError`
- `submit_guess()` when in `LOST` → raises `InvalidStateError`
- `start_game()` when already `PLAYING` → raises `InvalidStateError`

**Boundary**
- Exactly 6 guesses without winning → `LOST` (not on guess 5, not on guess 7)
- Correct guess on row 1 (first try) → `WON` immediately
- Correct guess on row 6 (last chance) → `WON` (not `LOST`)

**Done when:** all tests pass, 100% line and branch coverage on `state_machine.py`.

---

## [x] Phase 3 — UI Components

### [x] Step 1 — Board

Renders the 6×5 tile grid. Reacts to two events: a letter being typed, and a guess being submitted with results.

Each tile has three visual states:
- Empty — no letter, light border
- Typed — has a letter, dark border, white background
- Revealed — colored background (green/yellow/grey), white text

#### UI tests — `tests/ui/test_board.py`

Setup: each test creates a fresh `tk.Tk()` root and a `Board` instance, then calls `root.destroy()` in teardown.

**Typing**
- After `board.set_letter(row=0, col=0, letter="A")`: tile shows "A", border is dark
- After `board.clear_letter(row=0, col=0)`: tile shows "", border reverts to light
- Typing past column 4 has no effect (no 6th tile)

**Revealing**
- After `board.reveal_row(row=0, results=[...])`: each tile has the correct background color
  - `correct` → green
  - `present` → yellow
  - `absent` → grey
- Reveal does not affect other rows

**Reset**
- After `board.reset()`: all tiles are empty with light borders and white backgrounds

**Done when:** all tests pass, 90%+ line coverage on `board.py`.

---

### [x] Step 2 — Keyboard

Renders the on-screen QWERTY keyboard. Keys update color to reflect the best known result for each letter. Fires a callback when a key is clicked.

#### UI tests — `tests/ui/test_keyboard.py`

**Initial state**
- All 26 letter keys are present
- ENTER and backspace keys are present
- All keys have the default (unused) background color

**Color updates**
- After `keyboard.update_key("A", "correct")`: A key is green
- After `keyboard.update_key("A", "present")`: A key is yellow
- After `keyboard.update_key("A", "absent")`: A key is grey
- A key already `correct` does not downgrade to `present` or `absent` on a later call
- A key already `present` does not downgrade to `absent` on a later call
- A key already `absent` can upgrade to `present` or `correct`

**Click callback**
- Clicking a letter key fires the registered `on_letter` callback with the correct letter
- Clicking ENTER fires the registered `on_enter` callback
- Clicking backspace fires the registered `on_backspace` callback

**Reset**
- After `keyboard.reset()`: all keys return to default color

**Done when:** all tests pass, 90%+ line coverage on `keyboard.py`.

---

## [x] Phase 4 — Integration & Polish

### [x] Step 1 — App wiring & integration tests

Wire all components together in `app.py`. The App creates the window, instantiates components, and connects them: input events → StateMachine → Board + Keyboard updates.

#### Integration tests — `tests/ui/test_integration.py`

**Full winning game**
- Simulate typing the answer letter by letter + Enter
- Assert all tiles in that row are green
- Assert win message is displayed

**Full losing game**
- Simulate 6 incorrect guesses
- Assert the answer is revealed in the message

**Partial game flow**
- Type 3 letters → backspace → type a different letter → confirm only 3 letters are shown in the correct tiles

**Keyboard coloring tracks best result**
- After a guess, on-screen key colors match the best result seen so far for each letter

**New game**
- After a game ends, trigger new game
- Assert all tiles are empty, all keyboard keys are default color, state is reset

**Input blocked during wrong state**
- Typing while in `IDLE` (before game starts) has no effect
- Typing while in `WON` or `LOST` has no effect

**Done when:** all integration tests pass.

---

### [x] Step 2 — Final polish & coverage report

- Run `pytest --cov=src --cov-report=term-missing`
- Confirm coverage meets the thresholds from the Coverage Criteria table at the top
- Fix any uncovered lines or missing edge case tests
- Manually play one full game to confirm the UI feels correct

**Done when:** coverage thresholds met, game is playable end to end.
