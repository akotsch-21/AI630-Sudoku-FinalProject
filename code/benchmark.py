"""
Module used to benchmark Killer Sudoku solvers.
"""

import time
import copy
import os
import csv
from typing import Literal
from models.board import Board
from models.backtracking import backtracking, backtrackModified
from models.ml_solver import solve_with_model, load_candidate_ranker

def load_boards(n: int, difficulty: Literal[2, 3, 4]) -> list[Board]:
    """
    Load n random Killer Sudoku puzzles into a list of Board objects.

    Args:
        n: The number of puzzles to load.
        difficulty: The difficulty level of the puzzles to load.

    Returns:
        list[Board]: A list of Board objects representing the loaded puzzles.
    """
    return [Board.load_random_puzzle(difficulty=difficulty) for _ in range(n)]

def benchmark_backtracking(boards: list[Board]) -> list[float]:
    """
    Benchmark the Backtracking algorithm on a list of Board objects.

    Args:
        boards: A list of Board objects to benchmark.

    Returns:
        list[float]: A list of execution times for each board.
    """
    times = []
    for board in boards:
        start = time.time()
        backtracking(board, 0,0,0)
        end = time.time()
        times.append(end - start)
        board.reset()
    return times

def benchmark_backtracking_modified(boards: list[Board]) -> tuple[list[float], list[int]]:
    """
    Benchmark the modified backtracking algorithm on a list of Board objects.

    Args:
        boards: A list of Board objects to benchmark.

    Returns:
        tuple[list[float], list[int]]: A tuple containing a list of execution times and a list of backtracks saved for each board.
    """
    times = []
    backtracks = []
    for board in boards:
        boardmod = copy.deepcopy(board)
        required_backtracks = board.backtrack_calls

        start = time.time()
        _, backtracks_count = backtrackModified(boardmod, boardmod.select_unassigned_cell(), 0)
        end = time.time()
        backtracks.append(required_backtracks - backtracks_count)
        times.append(end - start)
        board.reset()

    return times, backtracks

def benchmark_backtracking_ml(boards: list[Board]) -> list[float]:
    """
    Benchmark the backtracking algorithm with machine learning heuristics on a list of Board objects.

    Args:
        boards: A list of Board objects to benchmark.

    Returns:
        list[float]: A list of execution times for each board.
    """
    times = []
    model = load_candidate_ranker()["model"]
    for board in boards:
        start = time.time()
        solve_with_model(board, model=model)
        end = time.time()
        times.append(end - start)
        board.reset()
    return times


if __name__ == "__main__":
    N = 100
    DIFFICULTY = int(os.getenv("DIFFICULTY", "3"))
    BOARDS = load_boards(N, DIFFICULTY)
    RESULTS_DIR = "tmp/benchmark_results"

    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f"Benchmarking {N} boards of difficulty {DIFFICULTY}...")
    print("Benchmarking Backtracking...")
    timeBacktrack = benchmark_backtracking(BOARDS)
    print("Benchmarking Modified Backtracking...")
    timeBacktrackMod, backtracksSaved = benchmark_backtracking_modified(BOARDS)
    print("Benchmarking ML Backtracking...")
    timeBacktrackML = benchmark_backtracking_ml(BOARDS)
    with open(os.path.join(RESULTS_DIR, f"benchmark_{DIFFICULTY}.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(["Board Index", "Time Backtrack", "Time ML Backtrack","Time Backtrack Modified", "Backtrack Modified Saved backtracks"])
        for i in range(N):
            writer.writerow([i, timeBacktrack[i], timeBacktrackML[i], timeBacktrackMod[i], backtracksSaved[i]])




    print(f" For {N} killer sudoku problems of difficulty {DIFFICULTY}:")
    print(f" Average Time for Backtrack Modified: {sum(timeBacktrackMod)/N:.2f}\n",
            f"Average Time for Normal Backtrack  : {sum(timeBacktrack)/N:.2f}\n",
            f"Average Time for ML Backtrack      : {sum(timeBacktrackML)/N:.2f}\n",
            f"Average Backtrack Saved            : {sum(backtracksSaved)/N}")
