# CAI3101 - Pure-Python Game AI Engine (with Bonus Features)

Pure-Python game engine and AI algorithms (Minimax, Alpha-Beta Pruning with move ordering, and chess-engine style post-game review) for three classical board games: **Tic-Tac-Toe (XO)**, **Connect 4**, and **Seega**.

Developed for university course **CAI3101**. Implemented strictly using the Python 3.10+ standard library (with `pytest` for testing and `fastapi`/`uvicorn` for the interactive web UI).

---

## 📁 Project Architecture

```
.
├── engine/
│   ├── __init__.py
│   ├── base.py            # Abstract class Game (immutable states, player normalization)
│   ├── search.py          # Minimax, Alpha-Beta, best_move, score_all_moves, iterative deepening
│   ├── levels.py          # Difficulty level to search depth mappings (easy, medium, hard, expert)
│   ├── api.py             # Stateless backend entry points (PvE, PvP, hint, eval, analyze)
│   ├── analysis.py        # Post-game analysis engine (loss calculation, move classification, accuracy)
│   ├── tree_viz.py        # Alpha-Beta Search Tree generator with pruning flags
│   ├── zobrist.py         # 64-bit Zobrist Hashing & Transposition Table for Connect 4
│   ├── benchmark.py       # Benchmark comparison suite & AI vs AI runner
│   └── games/
│       ├── __init__.py
│       ├── xo.py          # Tic-Tac-Toe engine (3x3)
│       ├── connect4.py    # Connect 4 engine (6x7 gravity board)
│       └── seega.py       # Ancient Egyptian Seega engine (5x5, 2-phase)
├── tests/
│   ├── test_search.py     # Minimax vs Alpha-Beta equivalence across 100+ positions per game
│   ├── test_step0.py      # Perspective symmetry and score_all_moves verification
│   ├── test_features.py   # Friends mode, Hint, Analysis blunder test, Tree Viz, Zobrist TT
│   ├── test_xo.py         # XO mechanics, win lines, exhaustive hard AI invincibility check
│   ├── test_connect4.py   # Gravity, full columns, 4 win directions, draw
│   ├── test_seega.py      # Placement rules, sandwich captures, center immunity, pass rule
│   └── test_api.py        # Stateless API validation and error handling
├── app/
│   ├── server.py          # FastAPI server (thin wrapper over engine/api.py)
│   └── static/
│       └── index.html     # Single-file UI (Play, Review, Benchmark, AI vs AI, Tree Viz)
├── results/               # Auto-generated benchmark JSON and CSV exports
├── REPORT_NOTES.md        # Mathematical formulas, analysis thresholds, and benchmark data
├── HANDOFF.md             # Complete project handover and architectural documentation
└── README.md
```

---

## 🚀 Installation & Requirements

- **Python 3.10+** (Python 3.11+ recommended)
- Standard library dependencies only for the engine core.
- Testing & UI dependencies:
  ```bash
  pip install pytest fastapi uvicorn
  ```

---

## 🧪 Running the Test Suite

Run all 51 test suites with pytest:
```bash
python -m pytest -v
```

Run specific test modules:
```bash
# Test perspective symmetry & score_all_moves (Step 0)
python -m pytest tests/test_step0.py -v

# Test new features (Friends mode, Hint, Post-game analysis blunder check, TT, Tree Viz)
python -m pytest tests/test_features.py -v

# Test search equivalence (Minimax vs Alpha-Beta across 100+ positions per game)
python -m pytest tests/test_search.py -v

# Test XO game tree and exhaustive invincibility check
python -m pytest tests/test_xo.py -v

# Test Connect 4 gravity, win lines, and draw states
python -m pytest tests/test_connect4.py -v

# Test Seega 2-phase rules, captures, passes, and 40-move counter
python -m pytest tests/test_seega.py -v

# Test stateless API endpoints
python -m pytest tests/test_api.py -v
```

---

## 🎮 Running the Web Interface

Start the lightweight FastAPI testing server:
```bash
python -m uvicorn app.server:app --reload --port 8000
```
Then open your browser at **[http://localhost:8000](http://localhost:8000)**.

### Features & Tabs:
1. **Play Game Tab**:
   - **Game Modes**: Human vs Computer (PvE) or Friends (hot-seat PvP).
   - **Split-Screen Layout**: Interactive board on the left; tools and telemetry on the right.
   - **Hints**: Click `💡 Hint` to highlight the best move, see column evaluation heatmaps in Connect 4, or destination arrows in Seega (3 hints per game).
   - **Live Eval Bar**: Toggleable real-time win-probability bar.
   - **Undo / Redo & Save / Load**: 1-click step undo/redo, plus JSON export and import.
   - **Forced Win Detector**: Detects and highlights forced win states.
2. **Game Review Tab (Post-Game Analysis)**:
   - When a match finishes, click `🔍 Analyze Game`.
   - Computes per-player Accuracy % and counts of Best, Good, Inaccuracy, Mistake, and Blunder moves.
   - Flags the single **Critical Moment** (biggest blunder of the match).
   - Interactive canvas evaluation-over-time line chart.
   - Click any move in the history to jump the board, view played vs best move highlights, and read engine explanations.
3. **Search Tree Tab (XO Visualizer)**:
   - Expandable hierarchical view of the Alpha-Beta call tree showing $\alpha, \beta$, values, and pruned branches.
4. **Benchmark Tab**:
   - Empirical comparison suite measuring Minimax vs Alpha-Beta vs Ordered Alpha-Beta.
5. **AI vs AI Tab**:
   - Automated step-by-step match simulator between two AI algorithms.

---

## 🌐 API Endpoints

- `GET /api/games` -> List supported games.
- `POST /api/{game}/new` -> Start game (supports `first_player` and `mode`).
- `POST /api/{game}/move` -> Apply move (supports PvE and hot-seat PvP).
- `POST /api/{game}/ai-move` -> Calculate and apply computer move.
- `POST /api/{game}/hint` -> Return best move recommendation and candidate scores.
- `POST /api/{game}/analyze` -> Post-game analysis report across all moves.
- `POST /api/{game}/eval` -> Live evaluation of current state.
- `POST /api/{game}/tree-viz` -> Return Alpha-Beta recursive call tree.
- `GET /api/benchmark/{game}?n=20` -> Run benchmark comparison suite.
- `POST /api/ai-vs-ai` -> Simulate automated match between two algorithms.
