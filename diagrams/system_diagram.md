# System Diagram: Game Glitch Investigator (Race the AI)

```mermaid
flowchart TD
    %% ---------- Humans ----------
    Player(["👤 Player"])
    Dev(["🧑‍💻 Developer / Reviewer"])

    %% ---------- UI layer ----------
    subgraph UI["app.py: Streamlit UI and session state"]
        Settings["Sidebar settings<br/>difficulty, AI level"]
        Form["Guess form<br/>text input, Submit, New Game"]
        State[("st.session_state<br/>secret, attempts, history,<br/>AI window and history, wins")]
        Render["Render: hints, attempts left,<br/>result banner, scoreboard,<br/>AI guess log after game ends"]
        Debug["Developer Debug Info expander<br/>(shows the secret)"]
    end

    %% ---------- Logic layer ----------
    subgraph Logic["logic_utils.py: pure game logic"]
        Range["get_range_for_difficulty"]
        Parse["parse_guess<br/>validate input"]
        Check["check_guess<br/>Win / Too High / Too Low"]
        Score["update_score"]
        subgraph AI["AI opponent"]
            Next["ai_next_guess<br/>Rookie: random in window<br/>Pro: binary search"]
            Narrow["narrow_range<br/>shrink window from hint"]
        end
        Race["determine_race_result<br/>user / ai / tie / none / continue"]
    end

    %% ---------- Testing ----------
    subgraph Tests["tests/test_game_logic.py (pytest)"]
        Unit["18 unit tests: hints, range narrowing,<br/>AI always finds secret, Pro ≤ 7 tries,<br/>race outcomes"]
        Results["test_results.txt"]
    end

    Notes["ai_interactions.md, reflection.md<br/>notes on AI-assisted changes"]

    %% ---------- Data flow: one round ----------
    Player -->|"1. picks settings"| Settings
    Settings --> Range
    Range -->|"range"| State
    Player -->|"2. types a guess"| Form
    Form -->|"raw text"| Parse
    Parse -->|"valid int, or error shown to player"| Check
    State -->|"secret"| Check
    Check -->|"user outcome"| Score
    Check -->|"user outcome"| Race
    Score -->|"score"| State

    State -->|"AI window (low, high)"| Next
    Next -->|"AI guess"| Check
    Check -->|"AI outcome (hint only)"| Narrow
    Narrow -->|"smaller window"| State
    Check -->|"AI outcome"| Race

    Race -->|"result and tally"| State
    State --> Render
    Render -->|"3. hint, result, AI log"| Player

    %% ---------- Human / testing checks on AI results ----------
    Player -.->|"checks: is the hint right? did the AI play fairly? (guess log revealed at game end)"| Render
    Dev -.->|"inspects secret and AI window"| Debug
    State -.-> Debug
    Dev -->|"runs pytest"| Unit
    Unit -.->|"verifies"| Parse
    Unit -.->|"verifies"| Check
    Unit -.->|"verifies"| Next
    Unit -.->|"verifies"| Narrow
    Unit -.->|"verifies"| Race
    Unit --> Results
    Dev -.->|"reviews AI-written code and records findings"| Notes
```

## Reading the diagram

- **Solid arrows** are the data flow for one round: the player's guess is parsed, checked against the secret, and scored. Right after it, the AI picks its own guess, gets only the Higher/Lower hint, and narrows its search window. Both outcomes go to `determine_race_result`, and the state is rendered back to the player.
- **Dotted arrows** are the human and testing checkpoints:
  - The **player** sees the hints and, once the game ends, the AI's full guess log, so they can check that the AI played fairly.
  - The **developer** uses the Debug expander to inspect the secret and AI state, runs **pytest** against the logic functions (including the AI and race rules), and reviews AI-written code, recording the findings in the notes files.
- All game rules live in `logic_utils.py` with no Streamlit dependency, which is what makes them testable. `app.py` only wires the UI to those functions and holds session state.
