if __name__ == "__main__":
    from models.board import Board
    from models.backtracking import backtracking
    board = Board.load_random_puzzle(difficulty=4)
    print(board)
    domain = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    backtracking(board, domain)
