"""Tabular-feature + MLP baseline for Killer Sudoku."""

from __future__ import annotations

import argparse
import copy
import random
from pathlib import Path
from typing import Any

import duckdb
import joblib
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from models.board import Board
from models.cell import Cell
from models.dataset import ensure_local_parquet


NEGATIVES_PER_POSITIVE = 3
MODEL_PATH = (Path(__file__).resolve().parents[2] / "data" / "mlp_candidate_ranker.joblib").as_posix()
RANDOM_SEED = 42
TRAIN_PUZZLE_COUNT = 100
TRAIN_STATES_PER_PUZZLE = 8
TRAIN_MAX_REVEALED_CELLS = 36
SOLVE_DIFFICULTY = 2
SOLVE_MAX_NODES = 50_000


def extract_candidate_features(board: Board, cell: Cell, candidate: int) -> list[float]:
    """Convert a (board, cell, candidate) triple into numeric features."""
    peer_filled = sum(1 for peer in board.arcs[cell] if peer.value is not None)
    cage_target = 0
    cage_remaining_after_assign = 0
    cage_unassigned_after_assign = 0
    if cell.cage is not None:
        cage = cell.cage
        assigned_sum = sum(other.value for other in cage.cells if other.value is not None and other != cell)
        cage_target = cage.target_sum
        cage_remaining_after_assign = cage.target_sum - (assigned_sum + candidate)
        cage_unassigned_after_assign = sum(1 for other in cage.cells if other.value is None and other != cell)

    return [
        float(cell.row),
        float(cell.col),
        float(candidate),
        float(len(cell.domains)),
        float(peer_filled),
        float(cage_target),
        float(cage_remaining_after_assign),
        float(cage_unassigned_after_assign),
    ]


def rank_candidates_for_cell(board: Board, cell: Cell, model: Any) -> list[int]:
    """Return candidate values sorted by model confidence (high to low)."""
    candidates = sorted(cell.domains)
    if len(candidates) <= 1:
        return candidates

    feature_rows = [extract_candidate_features(board, cell, candidate) for candidate in candidates]
    feature_matrix = np.asarray(feature_rows, dtype=float)
    probabilities = model.predict_proba(feature_matrix)
    scores = probabilities[:, 1] if probabilities.ndim == 2 and probabilities.shape[1] >= 2 else probabilities.ravel()

    ranked = sorted(zip(candidates, scores), key=lambda item: (item[1], -item[0]), reverse=True)
    return [candidate for candidate, _ in ranked]


def build_training_dataset() -> tuple[np.ndarray, np.ndarray]:
    """Build a binary dataset for candidate ranking."""
    rng = random.Random(RANDOM_SEED)

    parquet_source = ensure_local_parquet()
    query = f"""
        SELECT puzzle_string, difficulty, first_solution
        FROM "{parquet_source}"
        ORDER BY RANDOM()
        LIMIT {TRAIN_PUZZLE_COUNT}
    """
    rows = duckdb.query(query).fetchall()

    X: list[list[float]] = []
    y: list[int] = []

    for puzzle_string, row_difficulty, solution in rows:
        row_difficulty = int(row_difficulty)
        for _ in range(TRAIN_STATES_PER_PUZZLE):
            board = Board.from_puzzle_string(puzzle_string, difficulty=row_difficulty)

            reveal_count = rng.randint(0, TRAIN_MAX_REVEALED_CELLS)
            reveal_positions = rng.sample(range(81), k=reveal_count)

            for pos in reveal_positions:
                row, col = divmod(pos, 9)
                value = int(solution[row][col])
                cell = board.cells[row][col]
                cell.value = value
                cell.domains = {value}

            if not board.propagate_constraints():
                continue

            rows_by_label = {1: [], 0: []}

            for cell in board.iter_cells():
                if cell.value is not None:
                    continue

                target_value = int(solution[cell.row][cell.col])
                for candidate in sorted(cell.domains):
                    features = extract_candidate_features(board, cell, candidate)
                    rows_by_label[1 if candidate == target_value else 0].append(features)

            positive_rows = rows_by_label[1]
            if not positive_rows:
                continue

            X.extend(positive_rows)
            y.extend([1] * len(positive_rows))

            negative_rows = rows_by_label[0]
            rng.shuffle(negative_rows)
            keep_negatives = min(len(negative_rows), NEGATIVES_PER_POSITIVE * len(positive_rows))
            X.extend(negative_rows[:keep_negatives])
            y.extend([0] * keep_negatives)

    label_set = set(y)
    if label_set != {0, 1}:
        raise RuntimeError(
            f"Expected both classes [0, 1], got {sorted(label_set)}. "
            "Try increasing TRAIN_PUZZLE_COUNT or TRAIN_STATES_PER_PUZZLE."
        )

    return np.asarray(X, dtype=float), np.asarray(y, dtype=int)


def train_candidate_ranker() -> dict[str, float]:
    """Train and persist an MLP candidate-ranker model."""
    X, y = build_training_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=y,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPClassifier(
                    hidden_layer_sizes=(64, 32),
                    activation="relu",
                    solver="adam",
                    max_iter=250,
                    random_state=RANDOM_SEED,
                    early_stopping=True,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "train_samples": float(len(X_train)),
        "test_samples": float(len(X_test)),
    }

    output_path = Path(MODEL_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "metrics": metrics}, output_path)
    return metrics


def load_candidate_ranker() -> dict[str, Any]:
    """Load a previously saved model bundle."""
    bundle = joblib.load(MODEL_PATH)
    if isinstance(bundle, dict) and "model" in bundle:
        return bundle
    raise ValueError(f"Unexpected model file format at {MODEL_PATH}. Re-run `python code/ml_main.py train`.")


def solve_with_model(board: Board, model: Any, max_nodes: int = SOLVE_MAX_NODES) -> tuple[Board | None, int]:
    """Solve a board with model-guided depth-first search."""
    stack = [copy.deepcopy(board)]
    nodes = 0

    while stack:
        state = stack.pop()
        nodes += 1
        if nodes > max_nodes:
            return None, nodes

        if not state.propagate_constraints():
            continue

        if state.is_solved():
            return state, nodes

        cell = state.select_unassigned_cell()
        if cell is None:
            return state, nodes

        for candidate in reversed(rank_candidates_for_cell(state, cell, model=model)):
            if not state.is_valid(cell, candidate):
                continue

            child = copy.deepcopy(state)
            child_cell = child.cells[cell.row][cell.col]
            child_cell.value = candidate
            child_cell.domains = {candidate}
            stack.append(child)

    return None, nodes


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MLP baseline for Killer Sudoku candidate ranking.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("train", help="Train and save a candidate-ranker model.")
    subparsers.add_parser("solve", help="Solve a random puzzle with optional ML guidance.")

    return parser


if __name__ == "__main__":
    cli = build_cli()
    args = cli.parse_args()

    if args.command == "train":
        metrics = train_candidate_ranker()
        print("Training complete.")
        print(f"accuracy: {metrics['accuracy']:.4f}")
        print(f"train_samples: {int(metrics['train_samples'])}")
        print(f"test_samples: {int(metrics['test_samples'])}")
        print(f"Saved model to: {MODEL_PATH}")
    else:
        board = Board.load_random_puzzle(difficulty=SOLVE_DIFFICULTY)
        solved_board, nodes = solve_with_model(board, model=load_candidate_ranker()["model"])
        if solved_board is None:
            print(f"No solution found within node budget ({SOLVE_MAX_NODES} nodes).")
        else:
            print(f"Solved in {nodes} search nodes.")
            for row in solved_board.cells:
                print(" ".join(str(cell.value) for cell in row))
