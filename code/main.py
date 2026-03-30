if __name__ == "__main__":
    import time

    from rich.live import Live
    from models.board import Board

    board = Board.load_random_puzzle(difficulty=4)
    print(f"Before revising {board}")
    # print(board)
    board.revise_arcs()
    print(f"Domains after revising {board}")
    # print(board)


    # with Live(board, refresh_per_second=20) as live:

    #     while not board.solved:
    #         board.revise_arcs()
    #         live.update(board, refresh=True)
    #         time.sleep(0.03)

    #     live.update(board, refresh=True)
