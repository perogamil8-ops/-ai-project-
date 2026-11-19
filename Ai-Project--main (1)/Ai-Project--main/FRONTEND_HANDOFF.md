# Frontend Developer Handoff — CAI3101 Game AI Engine

> **Project:** AAST CAI3101 — Board Game AI with Minimax & Alpha-Beta Pruning  
> **Games:** Tic-Tac-Toe (XO), Connect 4, Seega  
> **Backend:** FastAPI (`app/server.py`) wrapping a pure-Python engine  
> **Protocol:** Stateless REST (JSON). No WebSocket. The client owns the state and sends it with every request.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Architecture Overview](#2-architecture-overview)
3. [Player Identity Mapping](#3-player-identity-mapping)
4. [API Endpoints Reference](#4-api-endpoints-reference)
   - [GET /api/games](#get-apigames)
   - [POST /api/{game}/new](#post-apigamenew)
   - [POST /api/{game}/move](#post-apigamemove)
   - [POST /api/{game}/ai-move](#post-apigameai-move)
   - [POST /api/{game}/hint](#post-apigamehint)
   - [POST /api/{game}/analyze](#post-apigameanalyze)
   - [POST /api/{game}/eval](#post-apigameeval)
   - [POST /api/{game}/tree-viz](#post-apigametree-viz)
   - [GET /api/benchmark/{game}](#get-apibenchmarkgame)
   - [POST /api/ai-vs-ai](#post-apiai-vs-ai)
5. [Game State Schemas](#5-game-state-schemas)
6. [Move Formats per Game](#6-move-formats-per-game)
7. [Game Flow Sequences](#7-game-flow-sequences)
8. [Game Modes](#8-game-modes)
9. [Hint System (UI Guide)](#9-hint-system-ui-guide)
10. [Post-Game Analysis (UI Guide)](#10-post-game-analysis-ui-guide)
11. [Live Eval Bar](#11-live-eval-bar)
12. [Search Tree Visualizer](#12-search-tree-visualizer)
13. [Benchmark & AI vs AI](#13-benchmark--ai-vs-ai)
14. [Seega-Specific UI Requirements](#14-seega-specific-ui-requirements)
15. [Error Handling](#15-error-handling)
16. [Important Notes](#16-important-notes)

---

## 1. Quick Start

```bash
# Install
pip install fastapi uvicorn

# Run the server
cd "d:\College\Sem 5\AI\Project"
python -m uvicorn app.server:app --host 127.0.0.1 --port 8000 --reload

# Server is now at http://127.0.0.1:8000
# API base: http://127.0.0.1:8000/api/...
```

There is a **reference test UI** at `app/static/index.html` (served at `GET /`). It is a single-file, framework-free demo — your frontend replaces it.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  YOUR FRONTEND (browser)                        │
│  Sends JSON requests, holds the game state,     │
│  records move history for analysis              │
└──────────────────┬──────────────────────────────┘
                   │ HTTP (REST, JSON)
                   ▼
┌──────────────────────────────────────────────────┐
│  app/server.py  (FastAPI thin wrapper)           │
│  - Validates request shapes via Pydantic models  │
│  - Delegates to engine/api.py                    │
│  - Returns JSON responses or HTTP 400 errors     │
└──────────────────┬───────────────────────────────┘
                   │ Python function calls
                   ▼
┌──────────────────────────────────────────────────┐
│  engine/         (pure Python, no web code)       │
│  ├── api.py      – high-level stateless functions │
│  ├── search.py   – minimax, alphabeta, best_move  │
│  ├── analysis.py – post-game review               │
│  ├── tree_viz.py – search tree generator           │
│  ├── benchmark.py – perf comparison suite          │
│  └── games/      – xo.py, connect4.py, seega.py   │
└──────────────────────────────────────────────────┘
```

**Key principle:** The backend is **stateless**. The client stores the game state JSON and sends it back on every request. The server never remembers sessions.

---

## 3. Player Identity Mapping

The engine uses canonical player IDs internally:

| Internal ID  | XO symbol | Connect 4 color | Seega color | PvE label  | Friends label |
|-------------|-----------|-----------------|-------------|-----------|---------------|
| `"human"`   | X         | Red             | Black       | Human     | Player 1      |
| `"computer"`| O         | Yellow          | White       | Computer  | Player 2      |

In **Friends mode** both sides are human players, but the API still uses `"human"` / `"computer"` as IDs internally. Use the `player_labels` dict returned by `new_game` to get display names.

Aliases accepted for `first_player`: `"human"`, `"p1"`, `"player1"`, `"x"`, `"black"`, `"red"` → maps to `"human"`. `"computer"`, `"p2"`, `"player2"`, `"o"`, `"white"`, `"yellow"` → maps to `"computer"`.

---

## 4. API Endpoints Reference

**Base URL:** `http://localhost:8000`  
**Content-Type:** `application/json` for all POST bodies  
**`{game}` path parameter:** `"xo"` | `"connect4"` | `"seega"` (also accepts `"tictactoe"`, `"c4"`)

---

### GET /api/games

Returns the list of supported games.

**Response:**
```json
["xo", "connect4", "seega"]
```

---

### POST /api/{game}/new

Start a new game.

**Request body:**
```json
{
  "first_player": "human",          // optional, default "human"
  "mode": "human_vs_computer"       // optional: "human_vs_computer" | "friends" | "pvp" | "hotseat"
}
```

**Response (200):**
```json
{
  "game": "xo",
  "mode": "human_vs_computer",
  "state": { ... },                  // game state JSON (see §5)
  "status": "ongoing",
  "current_player": "human",
  "player_labels": {
    "human": "Human",                // or "Player 1" in friends mode
    "computer": "Computer"           // or "Player 2" in friends mode
  },
  "legal_moves": [ [0,0], [0,1], ... ],
  "winner": null,
  "winning_cells": [],
  "message": "Game started. Human plays first."
}
```

---

### POST /api/{game}/move

Apply a human player's move (or either player's move in Friends mode).

**Request body:**
```json
{
  "state": { ... },                  // current game state (required)
  "move": [0, 1],                    // the move to play (see §6 for format)
  "mode": "human_vs_computer",       // optional, default "human_vs_computer"
  "player": "human"                  // optional, for explicit turn validation
}
```

**Response (200):**
```json
{
  "state": { ... },                  // new game state after the move
  "status": "ongoing",               // "ongoing" or "terminal"
  "winner": null,                    // null, "human", "computer", or "draw"
  "winning_cells": [],               // list of winning cell coordinates, or []
  "message": "Computer's turn.",
  "current_player": "computer",
  "legal_moves": [ ... ]
}
```

---

### POST /api/{game}/ai-move

Ask the AI to compute and play its move.

**Request body:**
```json
{
  "state": { ... },                  // current state where it's computer's turn
  "algorithm": "alphabeta",          // optional: "minimax" | "alphabeta"
  "level": "hard"                    // optional: "easy" | "medium" | "hard"
}
```

**Response (200):**
```json
{
  "move": [1, 1],                    // the move the AI chose
  "nodes": 549,                      // states explored during search
  "time_ms": 12.34,                  // computation time in milliseconds
  "state": { ... },                  // new state after AI's move
  "status": "ongoing",
  "winner": null,
  "winning_cells": [],
  "message": "Human's turn.",
  "current_player": "human",
  "legal_moves": [ ... ]
}
```

**Note:** `move` can be `null` when the AI was blocked and had to pass (Seega).

---

### POST /api/{game}/hint

Get the AI's recommended move for the current player.

**Request body:**
```json
{
  "state": { ... },                  // current game state
  "algorithm": "alphabeta",          // optional
  "depth": null                      // optional, uses smart defaults if null
}
```

**Default depths:** XO = 9 (full), Connect4 = 4, Seega = 3.

**Response (200):**
```json
{
  "best_move": [1, 1],
  "scores_per_move": {
    "(0, 0)": 3.0,
    "(0, 1)": -10.0,
    "(1, 1)": 13.0,
    ...
  },
  "scores_list": [
    { "move": [0, 0], "score": 3.0 },
    { "move": [0, 1], "score": -10.0 },
    { "move": [1, 1], "score": 13.0 }
  ],
  "nodes": 1234,
  "time_ms": 45.6,
  "message": "Suggested move: (1, 1)"
}
```

**Seega placement phase:** Returns `best_move: null` and `message: "Hints are available in the movement phase."`.

**UI rendering guide:**
- **XO:** Highlight the suggested cell (glow/outline).
- **Connect 4:** Highlight the column; show a **score heatmap bar** above each column using `scores_list` (green = best, red = worst).
- **Seega movement:** Show an **arrow** from the piece's current position to the destination: `best_move = [[r1,c1],[r2,c2]]`.

---

### POST /api/{game}/analyze

Perform post-game analysis on a completed match (chess-engine-style review).

**Request body:**
```json
{
  "first_player": "human",          // who played first
  "mode": "human_vs_computer",      // the mode the game was played in
  "moves": [                        // ordered list of ALL moves played
    [0, 0],                          // move 1
    [1, 1],                          // move 2
    ...
  ],
  "depth_override": null             // optional analysis depth (defaults: XO=9, C4=5, Seega=4)
}
```

> **Important:** The frontend must record every move played during the game (including AI moves) in order. For Seega, record the AI's random placements too.

**Response (200):**
```json
{
  "game": "xo",
  "mode": "human_vs_computer",
  "eval_depth": 9,
  "total_moves": 7,
  "steps": [
    {
      "move_no": 1,
      "player": "human",
      "played": [0, 0],              // the move that was played
      "best": [1, 1],                // the best move available
      "played_score": 3.0,
      "best_score": 13.0,
      "classification": "Mistake",   // "Best" | "Good" | "Inaccuracy" | "Mistake" | "Blunder"
      "loss": 0.182,                 // win-probability loss [0.0–1.0]
      "eval_after": 0.231,           // P1 eval after move [-1.0 to +1.0]
      "state_after": { ... },        // board state after this move
      "comment": "..."               // optional (placement phase: "Placement phase move")
    },
    ...
  ],
  "player1": {
    "label": "Human",
    "accuracy": 85.3,                // accuracy percentage [0–100]
    "counts": {
      "Best": 3,
      "Good": 1,
      "Inaccuracy": 0,
      "Mistake": 1,
      "Blunder": 0
    }
  },
  "player2": {
    "label": "Computer",
    "accuracy": 99.1,
    "counts": { "Best": 3, "Good": 0, "Inaccuracy": 0, "Mistake": 0, "Blunder": 0 }
  },
  "critical_moment": {               // the worst mistake/blunder, or null
    "move_no": 1,
    "player": "human",
    "played": [0, 0],
    "best": [1, 1],
    "loss": 0.182,
    "classification": "Mistake"
  }
}
```

**Classification thresholds** (on win-probability loss Δp):

| Classification | Δp range            | Suggested color |
|---------------|---------------------|-----------------|
| Best          | ≤ 0.005 or same move | 🟢 Green        |
| Good          | ≤ 0.05              | 🔵 Blue-green   |
| Inaccuracy    | ≤ 0.12              | 🟡 Yellow       |
| Mistake       | ≤ 0.25              | 🟠 Orange       |
| Blunder       | > 0.25              | 🔴 Red          |

**UI ideas:**
- Accuracy percentage per player (like chess.com).
- Classification counts (bar chart or pie chart).
- Eval chart: plot `eval_after` for each move (line chart, range −1 to +1).
- Move navigator: step through moves, show the board, highlight the played move vs. the best move.
- Critical moment highlight.

---

### POST /api/{game}/eval

Get live position evaluation (for the eval bar during play).

**Request body:**
```json
{
  "state": { ... }
}
```

**Response (200):**
```json
{
  "score": 23.5,                     // raw heuristic score
  "eval_normalized": 0.312,          // normalized [-1.0, +1.0] (positive = P1 advantage)
  "p1_win_prob": 0.656,              // win probability for Player 1 [0.0, 1.0]
  "mover": "human"                   // who moves next
}
```

**UI rendering:**
- Show a vertical or horizontal bar.
- `p1_win_prob = 0.5` → even. `> 0.5` → P1 advantage. `< 0.5` → P2 advantage.
- Color the bar: Player 1 color fills from one end, Player 2 color from the other.
- Call this after every move to update the bar in real-time.

---

### POST /api/{game}/tree-viz

Generate a search tree visualization (recursive JSON tree).

**Request body:**
```json
{
  "state": { ... },
  "depth": 2                         // optional, default 2 (keep ≤ 3 for performance)
}
```

**Response (200):**
```json
{
  "move": null,                      // root node
  "player": "human",
  "depth": 2,
  "alpha_in": "-inf",
  "beta_in": "+inf",
  "value": 13.0,
  "pruned": false,
  "children": [
    {
      "move": [0, 0],
      "player": "computer",
      "depth": 1,
      "alpha_in": "-inf",
      "beta_in": "+inf",
      "value": 3.0,
      "pruned": false,
      "children": [ ... ]
    },
    {
      "move": [0, 2],
      "player": "computer",
      "depth": 1,
      "alpha_in": 3.0,
      "beta_in": "+inf",
      "value": null,
      "pruned": true,                // ← pruned by Alpha-Beta!
      "children": []
    }
  ]
}
```

**UI rendering:**
- Render as a tree diagram (D3.js, vis.js, or custom canvas).
- Color pruned nodes differently (gray/dashed).
- Show α/β values on each node.
- Max depth 3 recommended for readability.

---

### GET /api/benchmark/{game}

Run a benchmark comparison of Minimax vs Alpha-Beta vs Alpha-Beta+Ordering.

**Query parameters:**
- `n` (int, 1–100, default 20): number of random positions to test.

**Response (200):**
```json
{
  "game": "xo",
  "depth": 2,
  "n_positions": 20,
  "averages": {
    "avg_minimax_nodes": 125.3,
    "avg_minimax_time_ms": 1.23,
    "avg_alphabeta_nodes": 45.2,
    "avg_alphabeta_time_ms": 0.45,
    "avg_alphabeta_ordered_nodes": 32.1,
    "avg_alphabeta_ordered_time_ms": 0.33,
    "avg_reduction_pct": 63.9,
    "avg_ordered_reduction_pct": 74.4
  },
  "rows": [
    {
      "position": 1,
      "minimax_nodes": 130,
      "minimax_time_ms": 1.1,
      "alphabeta_nodes": 50,
      "alphabeta_time_ms": 0.5,
      "alphabeta_ordered_nodes": 35,
      "alphabeta_ordered_time_ms": 0.3,
      "same_move": true,
      "reduction_pct": 61.5,
      "ordered_reduction_pct": 73.1
    },
    ...
  ]
}
```

> ⚠ This can be slow for Connect 4 and Seega. Show a loading spinner.

---

### POST /api/ai-vs-ai

Run an AI vs AI simulation.

**Request body:**
```json
{
  "game": "xo",                      // required
  "algo_a": "minimax",               // optional: "minimax" | "alphabeta"
  "level_a": "medium",               // optional: "easy" | "medium" | "hard"
  "algo_b": "alphabeta",             // optional
  "level_b": "medium",               // optional
  "seed": 0                          // optional: RNG seed for reproducibility
}
```

**Response (200):**
```json
{
  "game": "xo",
  "winner": "draw",
  "winning_cells": [],
  "total_moves": 9,
  "history": [
    {
      "step": 1,
      "player": "human",             // "human" = AI-A, "computer" = AI-B
      "move": [1, 1],
      "nodes": 549,
      "time_ms": 5.4,
      "score": 0.0,
      "state": { ... }
    },
    ...
  ],
  "final_state": { ... }
}
```

---

## 5. Game State Schemas

### XO State

```json
{
  "board": [
    [null, "human", null],
    [null, "computer", null],
    [null, null, null]
  ],
  "player": "human"
}
```

- `board`: 3×3 array. Each cell is `null`, `"human"` (X), or `"computer"` (O).
- `player`: whose turn it is.
- Rows: 0 = top, 2 = bottom. Columns: 0 = left, 2 = right.

### Connect 4 State

```json
{
  "board": [
    [null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null],
    [null, null, null, null, null, null, null],
    [null, null, null, "human", null, null, null],
    [null, null, null, "computer", null, null, null]
  ],
  "player": "human"
}
```

- `board`: 6×7 array. Row 0 = top, row 5 = bottom. Gravity: pieces fall to the lowest empty row.
- Cell: `null`, `"human"` (Red), `"computer"` (Yellow).
- `player`: whose turn.

### Seega State

```json
{
  "board": [
    ["human", "computer", null, "human", "computer"],
    ["computer", "human", "computer", "human", "computer"],
    ["human", "computer", null, "computer", "human"],
    ["computer", "human", "computer", "human", "computer"],
    ["human", "computer", "human", "computer", "human"]
  ],
  "phase": "movement",
  "player": "computer",
  "first_placer": "human",
  "placed_this_turn": 0,
  "human_placed": 12,
  "computer_placed": 12,
  "no_capture_counter": 5,
  "human_pieces": 11,
  "computer_pieces": 12,
  "last_capture_count": 1,
  "last_captor": "computer"
}
```

| Field                 | Type          | Description                                                                |
|----------------------|---------------|----------------------------------------------------------------------------|
| `board`              | 5×5 array     | `null`, `"human"` (Black), `"computer"` (White)                           |
| `phase`              | string        | `"placement"` or `"movement"`                                              |
| `player`             | string        | Whose turn it is                                                           |
| `first_placer`       | string        | Who placed first (determines who moves first in Phase 2)                   |
| `placed_this_turn`   | 0 or 1        | How many pieces the current player has placed this turn (Phase 1 only)     |
| `human_placed`       | int (0–12)    | Total pieces placed by human                                               |
| `computer_placed`    | int (0–12)    | Total pieces placed by computer                                            |
| `no_capture_counter` | int (0–40)    | Consecutive moves without a capture. Game ends at 40.                      |
| `human_pieces`       | int           | Current number of human pieces on the board                                |
| `computer_pieces`    | int           | Current number of computer pieces on the board                             |
| `last_capture_count` | int           | How many pieces were captured on the last move (0 = none)                  |
| `last_captor`        | string\|null  | Who captured last (`"human"`, `"computer"`, or `null`)                     |

---

## 6. Move Formats per Game

| Game      | Phase      | Move Format                     | Example                        |
|-----------|------------|---------------------------------|--------------------------------|
| XO        | —          | `[row, col]`                    | `[0, 1]` (top-middle)         |
| Connect 4 | —          | `column` (integer 0–6)          | `3` (center column)           |
| Seega     | Placement  | `[row, col]`                    | `[0, 0]` (top-left)           |
| Seega     | Movement   | `[[r1, c1], [r2, c2]]`         | `[[2, 3], [2, 2]]` (move left)|

**All coordinates are 0-indexed.** Row 0 = top, Column 0 = left.

**Pass moves:** In Seega movement phase, if `legal_moves` is empty, the player is blocked and the engine handles the pass automatically. The frontend does **not** need to send a pass — just call `/ai-move` for the computer or display a "Blocked! Other player's turn" message for the human and proceed.

---

## 7. Game Flow Sequences

### 7.1 Human vs Computer (Standard PvE)

```
Frontend                              Backend
  │                                      │
  ├─ POST /api/{game}/new ──────────────►│
  │◄────── { state, legal_moves, ... } ──┤
  │                                      │
  │  [Human's turn — show board]         │
  ├─ POST /api/{game}/move { state, move } ──►│
  │◄────── { state, status, ... }  ──────┤
  │                                      │
  │  [If status == "ongoing" && current_player == "computer"]
  ├─ POST /api/{game}/ai-move { state, level } ──►│
  │◄────── { move, state, nodes, ... } ──┤
  │                                      │
  │  [Show AI's move, update board]      │
  │  [Repeat until status == "terminal"] │
  │                                      │
  │  [Optional: call /hint, /eval during play]
  │  [After game: call /analyze with recorded moves]
```

### 7.2 Friends Mode (Hot-Seat PvP)

Same as PvE, but:
- `mode: "friends"` in `/new`.
- Use `/api/{game}/move` for **both** players (never call `/ai-move`).
- Include `mode: "friends"` in every `/move` request.
- Both players can use `/hint`.

### 7.3 Seega Two-Phase Flow

```
Phase 1 — PLACEMENT:
  Players alternate placing 2 pieces each per turn (excluding center square (2,2)).
  Move = [row, col] for each piece (send 2 moves per turn).
  Computer placements in PvE are RANDOM (call /ai-move for each).
  After 24 total pieces placed → auto-transitions to Phase 2.

Phase 2 — MOVEMENT:
  The player who placed SECOND moves first.
  Move = [[from_r, from_c], [to_r, to_c]].
  After each move, check the response message for capture info.
  If a player has no legal moves, they are blocked → other player continues.
  Game ends when: a player has 0 pieces, OR 40 consecutive moves without capture.
```

---

## 8. Game Modes

| Mode                | `mode` value           | Description                              |
|--------------------|------------------------|------------------------------------------|
| Human vs Computer  | `"human_vs_computer"`  | Standard PvE (default)                   |
| Friends (Hot-Seat) | `"friends"`            | Two humans sharing the same screen       |
| AI vs AI           | (use `/api/ai-vs-ai`)  | Separate endpoint, automated simulation  |

**Friends mode aliases:** `"pvp"`, `"hotseat"` are also accepted.

---

## 9. Hint System (UI Guide)

### How to use

1. On the human's turn, the user clicks "Hint".
2. Frontend calls `POST /api/{game}/hint` with the current state.
3. Response contains `best_move` and `scores_per_move` / `scores_list`.

### UI rendering per game

**XO:**
- Highlight the `best_move` cell with a glow/pulse/outline.

**Connect 4:**
- Highlight the `best_move` column (drop zone).
- Show a **heatmap bar** above the board: one block per column, color-coded by score from `scores_list`.
  - Highest score → green, lowest → red, middle → yellow.

**Seega (movement):**
- Draw an **arrow** from `best_move[0]` (source) to `best_move[1]` (destination).

**Seega (placement):**
- No hint available. Show message: "Hints are available in the movement phase."

### Optional: Hint limit
You may implement a limit (e.g., 3 hints per game) with a remaining-hints counter in the UI.

---

## 10. Post-Game Analysis (UI Guide)

### Recording moves

The frontend **must** record every move during gameplay:

```javascript
// Pseudocode
let moveHistory = [];

// After each move (human or AI):
moveHistory.push(move);  // the raw move value
```

For Seega, include both human moves and AI random placements.

### Requesting analysis

After the game ends, call:
```
POST /api/{game}/analyze
{
  "first_player": "human",    // who went first
  "mode": "human_vs_computer",
  "moves": [ ... ],           // the recorded move list
  "depth_override": null       // optional
}
```

### Rendering the review

**Accuracy display:**
```
Human:    85.3%  |  3 Best, 1 Good, 0 Inacc, 1 Mistake, 0 Blunder
Computer: 99.1%  |  3 Best, 0 Good, 0 Inacc, 0 Mistake, 0 Blunder
```

**Eval chart:**
Plot `steps[].eval_after` as a line chart (x = move number, y = eval from −1 to +1).
- Above 0 → Player 1 (human) advantage.
- Below 0 → Player 2 (computer) advantage.
- Color the area: P1 color above center line, P2 color below.

**Move navigator:**
- Step through moves with ◄ / ► buttons.
- For each step, show:
  - The board at `state_after`
  - The move played (highlighted on board)
  - The best move (highlighted differently if different from played)
  - Classification badge with color
  - Score comparison: "Played: −10.0, Best: +13.0"

**Critical moment:**
If `critical_moment` is not null, show a "Jump to critical moment" button.

---

## 11. Live Eval Bar

Call `POST /api/{game}/eval` after every move to update a live evaluation bar.

**Rendering:**
- Use `p1_win_prob` (0.0 to 1.0).
- A horizontal or vertical bar, split into two colors.
- Left/top portion = P1 color, sized at `p1_win_prob * 100%`.
- Right/bottom portion = P2 color, sized at `(1 - p1_win_prob) * 100%`.
- Display percentage or `eval_normalized` as text.

```
Example: p1_win_prob = 0.65

███████████████████░░░░░░░░░░  65% Player 1
```

---

## 12. Search Tree Visualizer

Call `POST /api/{game}/tree-viz` with a state and depth (keep depth ≤ 3).

The response is a **recursive JSON tree**. Each node has:

| Field       | Type            | Description                                     |
|------------|-----------------|--------------------------------------------------|
| `move`     | move \| null    | The move that led to this node (null for root)   |
| `player`   | string          | Current player at this node                      |
| `depth`    | int             | Remaining depth                                  |
| `alpha_in` | number\|string  | Alpha value when entering this node              |
| `beta_in`  | number\|string  | Beta value when entering this node               |
| `value`    | number\|null    | Minimax value (null if pruned)                   |
| `pruned`   | boolean         | Whether this node was pruned                     |
| `children` | array           | Child nodes (recursive)                          |

**Rendering tips:**
- Use a tree/graph library (D3.js tree layout, vis.js, or canvas).
- Color pruned nodes in gray/red with dashed border.
- Show α, β, and value labels on each node.
- Expandable/collapsible nodes for large trees.

---

## 13. Benchmark & AI vs AI

### Benchmark
- `GET /api/benchmark/{game}?n=20` — returns comparison data.
- Show results as a table or bar chart comparing Minimax vs Alpha-Beta vs Alpha-Beta+Ordering.
- Key metrics: node count, time, reduction percentage.

### AI vs AI
- `POST /api/ai-vs-ai` — runs a full game between two AIs.
- Show the game animated step-by-step.
- Display stats: nodes searched, time per move, final winner.

---

## 14. Seega-Specific UI Requirements

### Phase 1: Placement

- Show a 5×5 board. Center square (2,2) should be visually marked (star/icon) — it cannot be placed on.
- Each player places **2 pieces per turn**. After placing the first piece, show "Place your second piece" and keep it the same player's turn.
- Track `placed_this_turn` from the state to know if the player has 1 more to place.
- PvE: after human places 2, call `/ai-move` **twice** for the computer's 2 placements.
- Friends: alternate turns, each player places 2.
- Show piece counters: "Human: 5/12 placed | Computer: 4/12 placed".

### Phase 2: Movement

- **Piece selection → destination flow:** User clicks their piece (highlight it), then clicks an adjacent empty square.
- Allowed moves: up/down/left/right only (no diagonals). One step only.
- After a move, check the response `message` for capture info (e.g., "Computer captured 2 pieces!").
- **Center square immunity:** Visually indicate that a piece on (2,2) cannot be captured (special border/icon).
- **Blocked player:** If `legal_moves` is empty for a human player, show "You are blocked! Passing..." and immediately proceed to the other player's turn (or call `/ai-move` if it's the computer's turn).
- **Pieces counter:** Always show "Human: 11 | Computer: 12" (from `human_pieces`/`computer_pieces` in state).
- **40-move counter:** Optionally show "Moves without capture: 35/40" (from `no_capture_counter`).

### End conditions
- A player reaches 0 pieces → other player wins.
- 40 consecutive moves without capture → player with more pieces wins; equal = draw.

---

## 15. Error Handling

All endpoints return **HTTP 400** with a JSON body on client errors:

```json
{
  "detail": "Illegal move [0, 0]. Legal moves: [(0, 1), (1, 2), ...]"
}
```

Common errors:
| Error | Meaning |
|-------|---------|
| `"Unknown game 'xyz'"` | Invalid game name in URL |
| `"Game is already finished."` | Sent move/ai-move on a terminal state |
| `"Cannot apply human move when current player is 'computer'"` | Tried human move on computer's turn (PvE) |
| `"It is not X's turn."` | Player mismatch in friends mode |
| `"Illegal move ..."` | Move not in legal_moves |
| `"Column X is full"` | Connect 4: dropped in a full column |
| `"Center square (2, 2) cannot be placed on in Phase 1"` | Seega: tried placing on center |

**Always handle 400 responses gracefully in the UI** (toast notification or inline error).

---

## 16. Important Notes

1. **Stateless protocol:** The server does not store any game state. The frontend must keep the state JSON and send it back with every request. This means refreshing the page loses the game unless you persist state in `localStorage`.

2. **Move history recording:** You must maintain a list of all moves played (both human and AI) during the game to use the `/analyze` endpoint after the game ends.

3. **No WebSocket:** All communication is request/response. There is no server push. After requesting an AI move, the response contains the new state immediately (AI thinks synchronously).

4. **CORS:** The server allows all origins (`*`), so your frontend can run on any port/domain during development.

5. **Difficulty levels:** 
   - XO: easy (random), medium (depth 2), hard (full search — never loses)
   - Connect 4: easy (depth 1), medium (depth 3), hard (depth 5)
   - Seega: easy (depth 1), medium (depth 2), hard (depth 4) — movement phase only

6. **Algorithm choice:** `"minimax"` or `"alphabeta"`. Alpha-Beta is faster and returns the same move/score. Use Alpha-Beta for production; Minimax is available for educational comparison.

7. **Performance considerations:**
   - Connect 4 hard-level AI moves may take 1–3 seconds. Show a "thinking…" spinner.
   - Seega hard-level may take longer. Consider showing nodes/time from the response.
   - Benchmark endpoint can take 10–30 seconds. Use async/loading UI.
   - Tree-viz with depth > 3 generates huge responses. Limit to depth 2–3.

8. **Testing your integration:**
   ```bash
   # Quick smoke test
   curl -X POST http://localhost:8000/api/xo/new \
     -H "Content-Type: application/json" \
     -d '{"first_player": "human"}'
   ```

---

## Appendix: Running Tests

```bash
cd "d:\College\Sem 5\AI\Project"
python -m pytest tests/ -v
```

All 51 tests should pass. If you modify anything in `engine/`, re-run tests to verify nothing broke.
