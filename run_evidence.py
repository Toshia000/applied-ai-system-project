"""Reproducible evidence for grading: runs the real app headlessly and the AI logic.

Usage:  python run_evidence.py            (prints the log)
        python run_evidence.py > evidence_log.txt
Everything is deterministic: secrets are fixed and the Rookie AI uses a seeded RNG.
"""
import random
import sys

from streamlit.testing.v1 import AppTest

from logic_utils import (
    ai_next_guess,
    check_guess,
    get_range_for_difficulty,
    narrow_range,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ATTEMPTS = {"Easy": 10, "Normal": 8, "Hard": 5}


def new_app(difficulty="Normal", ai_level="Pro", secret=42):
    """Start the real Streamlit app and pin the secret so the run is repeatable."""
    at = AppTest.from_file("app.py", default_timeout=30).run()
    if difficulty != "Normal":
        at.selectbox[0].set_value(difficulty).run()
    if ai_level != "Rookie":
        at.selectbox[1].set_value(ai_level).run()
    at.session_state.secret = secret
    return at


def guess(at, text):
    at.text_input[0].set_value(text)
    at.button[0].click().run()
    assert not at.exception, at.exception
    return at


def banners(at):
    return [m.value for m in list(at.success) + list(at.error) + list(at.warning)]


def show(at, title, inputs, notes=""):
    print(f"\n### {title}")
    print(f"Input(s):  {inputs}")
    print(f"Output:    {banners(at)}")
    print(f"State:     status={at.session_state.status}, result={at.session_state.result}, "
          f"attempts={at.session_state.attempts}, ai_tries={len(at.session_state.ai_history)}")
    if notes:
        print(f"Check:     {notes}")


print("=" * 70)
print("SECTION 1: Example runs through the real Streamlit app (headless)")
print("=" * 70)

# 1. User wins: finds the secret on the first try, AI (Pro) needs more.
at = new_app(secret=42)
print(f"\nStart banner: {at.info[0].value}")
guess(at, "42")
show(at, "Run A - user beats the AI", "secret=42, user guesses 42 (try 1), AI=Pro",
     "user found it in 1 try; AI hadn't -> result 'user'")

# 2. AI wins: user keeps guessing 1, Pro binary-searches 42 in 7 tries.
at = new_app(secret=42)
for _ in range(8):
    if at.session_state.status != "playing":
        break
    guess(at, "1")
show(at, "Run B - AI beats the user", "secret=42, user guesses 1 every round, AI=Pro",
     "Pro's guesses 50,25,37,43,40,41,42 -> found on try 7 -> result 'ai'")
print("AI guess log:", [g for g, _ in at.session_state.ai_history])

# 3. Tie: secret is the midpoint, so Pro guesses it on try 1 as does the user.
at = new_app(secret=50)
guess(at, "50")
show(at, "Run C - tie", "secret=50, user guesses 50 (try 1), AI=Pro guesses 50 (try 1)",
     "both found it in the same round -> result 'tie'")

# 4. Nobody wins: Hard allows 5 tries, but Pro needs 6 for secret 2 (and the user guesses wrong).
at = new_app(difficulty="Hard", ai_level="Pro", secret=2)
for _ in range(5):
    if at.session_state.status != "playing":
        break
    guess(at, "50")
show(at, "Run D - out of attempts", "Hard (1-50, 5 tries), secret=2, user guesses 50 x5, AI=Pro",
     "Pro needs 6 tries for 2, the limit is 5 -> nobody finds it -> result 'none'")

print()
print("=" * 70)
print("SECTION 2: Guardrails (bad input and state resets)")
print("=" * 70)

at = new_app(secret=42)
for bad in ("abc", "", "  ", "4x2"):
    guess(at, bad)
    print(f"Input {bad!r:8} -> error={[e.value for e in at.error]}, attempts={at.session_state.attempts}")
assert at.session_state.attempts == 0, "invalid input must not use an attempt"
print("PASS: invalid input shows an error and does not use an attempt")

guess(at, "42")
finished = (at.session_state.status, at.session_state.result, at.session_state.attempts)
guess(at, "10")
assert (at.session_state.status, at.session_state.result, at.session_state.attempts) == finished
print("PASS: guesses after the game is over are ignored (state unchanged)")

at.button[1].click().run()
assert (at.session_state.status, at.session_state.attempts, at.session_state.ai_history) == ("playing", 0, [])
print("PASS: New Game resets status, attempts and AI history")

at = new_app(secret=42)
guess(at, "10")
at.selectbox[0].set_value("Easy").run()
assert at.session_state.attempts == 0 and get_range_for_difficulty("Easy") == (1, 20)
assert 1 <= at.session_state.secret <= 20
print("PASS: changing difficulty starts a fresh game inside the new range")

at = new_app(secret=42)
guess(at, "10")
assert not any("How the" in m.value for m in at.subheader), "AI log must stay hidden"
assert at.session_state.status == "playing"
print("PASS: AI guess log is not shown while the game is in progress")

print()
print("=" * 70)
print("SECTION 3: Reliability - AI vs every possible secret (seeded, deterministic)")
print("=" * 70)
print(f"{'Difficulty':<11}{'Range':<9}{'Limit':<7}{'AI':<8}{'Found in limit':<16}{'Avg tries':<11}{'Max tries'}")


def play(secret, low, high, level, rng, cap=1000):
    lo, hi, tries = low, high, 0
    while tries < cap:
        tries += 1
        g = ai_next_guess(lo, hi, level, rng)
        outcome, _ = check_guess(g, secret)
        if outcome == "Win":
            return tries
        lo, hi = narrow_range(lo, hi, g, outcome)
    raise AssertionError("AI never found the secret")


for diff in ("Easy", "Normal", "Hard"):
    lo, hi = get_range_for_difficulty(diff)
    for level in ("Pro", "Rookie"):
        rng = random.Random(0)
        runs = [play(s, lo, hi, level, rng) for s in range(lo, hi + 1) for _ in range(200)]
        within = sum(r <= ATTEMPTS[diff] for r in runs) / len(runs)
        print(f"{diff:<11}{f'{lo}-{hi}':<9}{ATTEMPTS[diff]:<7}{level:<8}{within:<16.0%}"
              f"{sum(runs) / len(runs):<11.2f}{max(runs)}")
print("\nPASS: with unlimited tries both AI levels found every secret (no run raised).")
