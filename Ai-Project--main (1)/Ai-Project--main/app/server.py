"""FastAPI server wrapping engine/api.py, analysis, and benchmark functions."""
from __future__ import annotations

import os
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine import api
from engine import benchmark
from engine import tree_viz

app = FastAPI(title="CAI3101 Game Engine Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class NewGameRequest(BaseModel):
    first_player: str = "human"
    mode: str = "human_vs_computer"


class HumanMoveRequest(BaseModel):
    state: dict[str, Any]
    move: Any
    mode: str = "human_vs_computer"
    player: str | None = None


class AIMoveRequest(BaseModel):
    state: dict[str, Any]
    algorithm: str = "alphabeta"
    level: str = "hard"


class HintRequest(BaseModel):
    state: dict[str, Any]
    algorithm: str = "alphabeta"
    depth: int | None = None


class AnalyzeRequest(BaseModel):
    first_player: str = "human"
    mode: str = "human_vs_computer"
    moves: list[Any] = []
    depth_override: int | None = None


class EvalRequest(BaseModel):
    state: dict[str, Any]


class TreeVizRequest(BaseModel):
    state: dict[str, Any]
    depth: int = 2


class AIvsAIRequest(BaseModel):
    game: str
    algo_a: str = "minimax"
    level_a: str = "medium"
    algo_b: str = "alphabeta"
    level_b: str = "medium"
    seed: int = 0


@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path)


@app.get("/api/games")
def get_games():
    return ["xo", "connect4", "seega"]


@app.post("/api/{game}/new")
def post_new_game(game: str, req: NewGameRequest):
    try:
        return api.new_game(game, req.first_player, mode=req.mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/{game}/move")
def post_human_move(game: str, req: HumanMoveRequest):
    try:
        return api.apply_human_move(game, req.state, req.move, mode=req.mode, player=req.player)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/{game}/ai-move")
def post_ai_move(game: str, req: AIMoveRequest):
    try:
        return api.ai_move(game, req.state, req.algorithm, req.level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/{game}/hint")
def post_hint(game: str, req: HintRequest):
    try:
        return api.hint(game, req.state, req.algorithm, req.depth)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/{game}/analyze")
def post_analyze(game: str, req: AnalyzeRequest):
    try:
        return api.analyze_game_match(
            game=game,
            first_player=req.first_player,
            moves=req.moves,
            mode=req.mode,
            depth_override=req.depth_override,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/{game}/eval")
def post_eval(game: str, req: EvalRequest):
    try:
        return api.eval_position(game, req.state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/{game}/tree-viz")
def post_tree_viz(game: str, req: TreeVizRequest):
    try:
        _, game_inst = api.get_game_instance(game)
        state_obj = game_inst.from_json(req.state)
        return tree_viz.build_search_tree(game_inst, state_obj, depth=req.depth)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/benchmark/{game}")
def get_benchmark(game: str, n: int = Query(20, ge=1, le=100)):
    try:
        _, game_inst = api.get_game_instance(game)
        return benchmark.run_suite(game_inst, n_positions=n)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/ai-vs-ai")
def post_ai_vs_ai(req: AIvsAIRequest):
    try:
        _, game_inst = api.get_game_instance(req.game)
        return benchmark.ai_vs_ai(
            game_inst,
            algo_a=req.algo_a,
            level_a=req.level_a,
            algo_b=req.algo_b,
            level_b=req.level_b,
            seed=req.seed,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
