if __name__ == "__main__":
    from models.board import Board
    from models.backtracking import backtraking
    board = Board.load_random_puzzle()
    print(board)
    domain = [1,2,3,4,5,6,7,8,9]
    backtraking(board,domain)
   
   
