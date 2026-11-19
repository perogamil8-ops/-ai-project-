# CAI3101 Project Report Notes: Game AI & Search Algorithms

This document provides a concise, formal explanation of the heuristic evaluation functions, search algorithms, empirical benchmarks, and advanced bonus features for the pure-Python board game engine developed for **CAI3101**. It is formatted for direct inclusion into project reports and technical presentations.

---

## 1. Heuristic Evaluation Functions

The game tree search employs heuristic evaluation functions when non-terminal cutoff depths are reached. All evaluation functions evaluate the position from the perspective of the specified player (by default **Computer / P2**, or the **player to move**), where positive values indicate an advantage and negative values indicate a disadvantage.

---

### 1.1 Tic-Tac-Toe (XO)

#### Heuristic Formula
For non-terminal cutoff states:
$$\text{Score} = \sum_{\text{line} \in \mathcal{L}} \text{Score}(\text{line}) + \text{CenterBonus}$$

Where $\mathcal{L}$ represents the 8 winning lines (3 horizontal, 3 vertical, 2 diagonal):
- **2 Own Pieces + 1 Empty Cell**: $+10.0$ (immediate winning threat)
- **1 Own Piece + 2 Empty Cells**: $+1.0$ (potential line of attack)
- **2 Opponent Pieces + 1 Empty Cell**: $-10.0$ (immediate defensive threat requiring blocking)
- **1 Opponent Piece + 2 Empty Cells**: $-1.0$ (opponent expansion)
- **Blocked Lines** (both player and opponent pieces present): $0.0$

#### Center Control
- $\text{CenterBonus} = +3.0$ if the center square $(1, 1)$ is held by Computer, $-3.0$ if held by Human, $0$ otherwise.

#### Terminal Utility
- Win for Computer: $+1000.0$
- Loss for Computer (Win for Human): $-1000.0$
- Draw: $0.0$

---

### 1.2 Connect 4

Connect 4 is played on a $6 \times 7$ vertical grid with 69 possible 4-in-a-row target windows (24 horizontal, 21 vertical, 12 down-right diagonal, 12 up-right diagonal).

#### Heuristic Formula
$$\text{Score} = \sum_{w \in \mathcal{W}} \text{Score}(w) + \sum_{r=0}^{5} \text{CenterColumn}(r, 3)$$

#### Window Evaluation Scoring $\text{Score}(w)$
For each 4-cell window $w$:
- **4 Own Coins**: $+100,000$ (win-level)
- **4 Opponent Coins**: $-100,000$ (loss-level)
- **3 Own Coins + 1 Empty**: $+50$ (strong attacking opportunity)
- **2 Own Coins + 2 Empty**: $+5$ (developing cluster)
- **3 Opponent Coins + 1 Empty**: $-80$ (**critical blocking priority**; heavily penalizes failing to block an imminent opponent 4-in-a-row)
- **2 Opponent Coins + 2 Empty**: $-5$ (opponent developing cluster)

#### Center Column Bonus
Column 3 (the vertical center axis) is geometrically critical because it participates in the maximum number of potential winning lines across the board.
- $+3.0$ per friendly coin in Column 3.
- $-3.0$ per opponent coin in Column 3.

#### Move Ordering Strategy
Move ordering arranges candidate columns in center-out priority: `[3, 2, 4, 1, 5, 0, 6]`. This ordering ensures alpha-beta pruning evaluates the highest-potential moves first, maximizing cutoffs.

---

### 1.3 Seega

Seega is played on a $5 \times 5$ board with 12 pieces per player. Search operates strictly in **Phase 2 (Movement)**.

#### Heuristic Formula
$$\text{Score} = 10 \cdot (\Delta \text{Pieces}) + 1 \cdot (\Delta \text{Mobility}) + \text{CenterBonus} + 0.5 \cdot (\Delta \text{Protected})$$

#### Component Definitions:
1. **Piece Difference ($\Delta \text{Pieces}$, weight $10.0$)**:
   $$\Delta \text{Pieces} = N_{\text{computer}} - N_{\text{human}}$$
   The dominant objective in Seega is unit elimination; material dominance directly dictates victory.
2. **Mobility Difference ($\Delta \text{Mobility}$, weight $1.0$)**:
   $$\Delta \text{Mobility} = \text{LegalMoves}_{\text{computer}} - \text{LegalMoves}_{\text{human}}$$
   Surrounding opponent pieces forces passes and limits enemy counter-attacks.
3. **Center Control Bonus ($\text{CenterBonus} = \pm 3.0$)**:
   The center square $(2, 2)$ is completely immune from capture and serves as the strategic pivot for multi-directional flanking.
   - $+3.0$ if Computer occupies $(2, 2)$
   - $-3.0$ if Human occupies $(2, 2)$
4. **Flanking Protection Bonus ($\Delta \text{Protected}$, weight $0.5$)**:
   Measures structural safety against sandwich captures along horizontal and vertical axes:
   - Immune Center $(2, 2)$: $+1.0$ safety score.
   - Horizontal Safety: $+0.5$ if the piece is against the board edge or anchored by a friendly adjacent piece.
   - Vertical Safety: $+0.5$ if the piece is against the board edge or anchored by a friendly adjacent piece.

---

## 2. Benchmark Comparison Table

The benchmark suite evaluated 50 sampled mid-game positions per game under standard test conditions using identical counting rules: **every recursive state visit increments the node counter by 1**.

### Summary Performance Table (50 Positions Each)

| Game | Search Depth | Minimax Avg Nodes | Alpha-Beta Avg Nodes | AB + Ordering Avg Nodes | Alpha-Beta Reduction | Ordered AB Reduction |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Tic-Tac-Toe (XO)** | 3 | **223.0** | 105.9 | **75.4** | $52.5\%$ | **$66.2\%$** |
| **Connect 4** | 3 | **394.8** | 186.7 | **127.9** | $52.7\%$ | **$67.6\%$** |
| **Seega** | 2 | **38.8** | 25.7 | **20.5** | $33.8\%$ | **$47.2\%$** |

---

## 3. Bonus Features & Architectural Enhancements

### 3.1 Perspective-Agnostic Search
The search architecture was refactored from a hardcoded `computer = MAX` assumption to a general **mover-centric perspective**:
- `best_move(game, state, algorithm, depth, perspective=None)`:
  When `perspective=None`, the search dynamically evaluates from the perspective of the player whose turn it is (`game.current_player(state)`).
- Canonical player aliases (`P1` = "human", `P2` = "computer") allow seamless hot-seat Friends mode where both players are human.
- **Perspective Symmetry Property**:
  For any state $s$:
  $$\text{Score}(s, \text{P1}) = -\text{Score}(s, \text{P2})$$

### 3.2 Full-Window Move Scoring (`score_all_moves`)
Standard Alpha-Beta pruning produces lower/upper bounds for non-principal variations. For move review, heatmaps, and hints, exact evaluations are required for all candidate moves.
- `score_all_moves(game, state, depth, perspective=None)` searches each legal move at the root with a full $(\alpha = -\infty, \beta = +\infty)$ window.
- The highest-scoring candidate is mathematically guaranteed to equal the move selected by `best_move`.

### 3.3 Post-Game Analysis Mathematical Formulation
Inspired by modern chess engine analysis (e.g. Chess.com, Lichess), every played move is reviewed:

1. **Win-Probability Normalization**:
   Raw scores are converted to a win probability $p \in [0.0, 1.0]$ using a logistic sigmoid:
   $$p(\text{Score}) = \frac{1}{1 + e^{-\text{Score} / k}}$$
   Where $k$ scales the sensitivity per game:
   - $k_{\text{XO}} = 10.0$ (a 2-in-a-row open threat shifts probability by $\sim 23\%$)
   - $k_{\text{Connect4}} = 50.0$ (an open 3-in-a-row shifts probability by $\sim 23\%$)
   - $k_{\text{Seega}} = 15.0$ (a 1-piece advantage shifts probability by $\sim 16\%$)
   - Forced wins ($\ge 900$) saturate to $p = 1.0$; forced losses ($\le -900$) saturate to $p = 0.0$.

2. **Win-Probability Loss**:
   $$\Delta p = \max(0, p(\text{BestScore}) - p(\text{PlayedScore}))$$

3. **Classification Thresholds**:
   | Classification | Condition | Description |
   | :--- | :--- | :--- |
   | **Best** | $\Delta p \le 0.005$ or identical move | Optimal engine move |
   | **Good** | $\Delta p \le 0.05$ | Strong move with negligible loss |
   | **Inaccuracy** | $\Delta p \le 0.12$ | Suboptimal choice leaving counterplay |
   | **Mistake** | $\Delta p \le 0.25$ | Significant loss of winning advantage |
   | **Blunder** | $\Delta p > 0.25$ | Critical error altering the match outcome |

4. **Player Accuracy Formula**:
   $$\text{Accuracy} = \max\left(0, \min\left(100, 100 \times (1 - \overline{\Delta p})\right)\right)$$
   Where $\overline{\Delta p}$ is the mean win-probability loss over all moves played by that player.

5. **Normalized Evaluation Metric**:
   $$\text{Eval}_{\text{normalized}} = 2 \cdot p(\text{Score}_{\text{P1}}) - 1 \in [-1.0, +1.0]$$
   $+1.0$ represents a completely winning position for Player 1, $-1.0$ for Player 2, and $0.0$ represents equal chances.

### 3.4 Zobrist Hashing & Transposition Table (Connect 4)
- A 64-bit Zobrist hash table assigns unique pseudorandom bitstrings to each cell and piece: $(r, c, \text{player})$.
- The state hash is updated with XOR operations: $H = \bigoplus (r, c, p) \oplus \text{TurnBit}$.
- Transpositions across different move orders (e.g. column 3 then 2 vs column 2 then 3) are cached with exact values, upperbounds, and lowerbounds, eliminating redundant subtree expansions.

### 3.5 Search Tree Visualizer (XO)
- Traverses and exports the Alpha-Beta recursive call tree as an annotated hierarchical JSON structure with $\alpha_{\text{in}}$, $\beta_{\text{in}}$, computed value, and `pruned: True` markers.
- Rendered visually in the web interface to demonstrate alpha-beta cutoffs in action.
