if __name__ == "__main__":
    from models.board import Board
    board = Board.load_random_puzzle()
    print(board)