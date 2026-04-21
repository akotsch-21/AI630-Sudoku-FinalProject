if __name__ == "__main__":
    import time
    import copy
    from rich.live import Live
    from models.board import Board
    from models.backtracking import backtracking
    from models.backtracking import backtrackModified

    board = Board.load_random_puzzle(difficulty=4)
    boardmod = copy.deepcopy(board)
    Fboard = copy.deepcopy(board)

    #print(f"Before revising {board}")
    # print(board)


    #print(f"Domains after revising {board}")
    # print(board)


    #board = backtracking(board, 0, 0)
    #print(f"After backtracking {board}")

    with Live(board, refresh_per_second=20) as live:
        start = time.time()

        #print(cell.row, cell.col, cell.domains.intersection(cell.cage.getDomain()))

        correct, backtracks = backtracking(board, 0,0,0) # normal backtracking

        end = time.time()

        #live.update(board, refresh=True)
        print(f"Backtracking: Time taken: {end - start:.2f} seconds, Backtracking calls saved: {board.backtrack_calls-backtracks}")

    with Live(boardmod, refresh_per_second=20) as live:
        start = time.time()

        #print(cell.row, cell.col, cell.domains.intersection(cell.cage.getDomain()))

        correct, backtracks = backtrackModified(boardmod, boardmod.select_unassigned_cell(),0) # normal backtracking

        end = time.time()

        #live.update(board, refresh=True)
        print(f"Backtracking Modified: Time taken: {end - start:.2f} seconds, Backtracking calls saved: {board.backtrack_calls-backtracks}")
