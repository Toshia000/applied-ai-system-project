import random
import streamlit as st
from logic_utils import (
    AI_LEVELS,
    ai_next_guess,
    check_guess,
    determine_race_result,
    get_range_for_difficulty,
    narrow_range,
    parse_guess,
    update_score,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("Race the AI: whoever finds the secret number in fewer tries wins.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

ai_level = st.sidebar.selectbox(
    "AI opponent",
    list(AI_LEVELS),
    index=0,
    help="Rookie guesses randomly inside the remaining range. "
    "Pro uses binary search and is very hard to beat.",
)

# FIX: Easier difficulties should allow more attempts
attempt_limit_map = {
    "Easy": 10,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")


def start_new_game():
    """Reset everything that belongs to a single round of the race."""
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.status = "playing"
    st.session_state.result = None
    st.session_state.history = []
    # The AI starts knowing only the range, exactly like the user.
    st.session_state.ai_history = []  # list of (guess, outcome)
    st.session_state.ai_low = low
    st.session_state.ai_high = high
    st.session_state.ai_solved = False


if "score" not in st.session_state:
    st.session_state.score = 0

if "wins" not in st.session_state:
    st.session_state.wins = {"user": 0, "ai": 0, "tie": 0}

# Changing difficulty or AI level starts a fresh game (new range, new secret).
game_config = (difficulty, ai_level)
if st.session_state.get("game_config") != game_config:
    start_new_game()
    st.session_state.game_config = game_config

scoreboard = st.sidebar.empty()
status_box = st.empty()

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)
    st.write("AI level:", ai_level)
    st.write("AI window:", (st.session_state.ai_low, st.session_state.ai_high))

st.subheader("Make a guess")

#FIX: Nest input inside the form, so when enter is pressed the form is submitted
with st.form("guess_form"):
    raw_guess = st.text_input(
        "Enter your guess:",
        key=f"guess_input_{difficulty}"
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        submit = st.form_submit_button("Submit Guess 🚀")
    with col2:
        new_game = st.form_submit_button("New Game 🔁")
    with col3:
        show_hint = st.checkbox("Show hint", value=True)

if new_game:
    start_new_game()
    st.rerun()

if submit and st.session_state.status == "playing":
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        # Invalid input doesn't use up an attempt, so the race stays fair.
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)
        attempts = st.session_state.attempts

        # FIX: Removed parsing even guess numbers to string
        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=attempts,
        )

        # The AI takes its turn right after the user, using only the hints.
        ai_guess = ai_next_guess(
            st.session_state.ai_low, st.session_state.ai_high, ai_level
        )
        ai_outcome, _ = check_guess(ai_guess, st.session_state.secret)
        st.session_state.ai_history.append((ai_guess, ai_outcome))
        st.session_state.ai_low, st.session_state.ai_high = narrow_range(
            st.session_state.ai_low, st.session_state.ai_high, ai_guess, ai_outcome
        )
        st.session_state.ai_solved = ai_outcome == "Win"

        result = determine_race_result(
            user_solved=outcome == "Win",
            ai_solved=st.session_state.ai_solved,
            attempts=attempts,
            attempt_limit=attempt_limit,
        )
        if result is not None:
            st.session_state.status = "over"
            st.session_state.result = result
            if result in st.session_state.wins:
                st.session_state.wins[result] += 1
            if result == "user":
                st.balloons()

# --- Status, scoreboard and results (rendered after processing so they're current) ---

attempts = st.session_state.attempts
status_box.info(
    f"Guess a number between {low} and {high}. "
    f"Your attempts left: {attempt_limit - attempts} · "
    f"🤖 AI tries so far: {len(st.session_state.ai_history)}"
)

wins = st.session_state.wins
scoreboard.caption(
    f"🏆 You: {wins['user']} · 🤖 AI: {wins['ai']} · 🤝 Ties: {wins['tie']}"
)

secret = st.session_state.secret
result = st.session_state.result
if result == "user":
    st.success(
        f"🏆 You beat the AI! You found {secret} in {attempts} tries "
        f"and the AI hadn't. Score: {st.session_state.score}"
    )
elif result == "ai":
    st.error(
        f"🤖 The AI wins! It found {secret} in {len(st.session_state.ai_history)} "
        f"tries, before you did. Score: {st.session_state.score}"
    )
elif result == "tie":
    st.success(f"🤝 It's a tie! You and the AI both found {secret} in {attempts} tries.")
elif result == "none":
    st.error(
        f"Out of attempts! Nobody found the secret, which was {secret}. "
        f"Score: {st.session_state.score}"
    )

# The AI's guesses would leak hints about the secret, so reveal them only when the game ends.
if st.session_state.status == "over":
    st.subheader(f"🤖 How the {ai_level} AI played")
    for i, (ai_guess, ai_outcome) in enumerate(st.session_state.ai_history, start=1):
        _, ai_message = check_guess(ai_guess, secret)
        st.write(f"Try {i}: **{ai_guess}** → {ai_message}")
    st.caption("Start a new game to race again.")

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
