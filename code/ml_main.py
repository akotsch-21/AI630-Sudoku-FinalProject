"""
Convenience entry point for the Killer Sudoku MLP baseline.
"""

from models.board import Board
from models.ml_solver import (
    MODEL_PATH,
    SOLVE_DIFFICULTY,
    SOLVE_MAX_NODES,
    build_cli,
    load_candidate_ranker,
    solve_with_model,
    train_candidate_ranker,
)


if __name__ == "__main__":
    parser = build_cli()
    args = parser.parse_args()
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
