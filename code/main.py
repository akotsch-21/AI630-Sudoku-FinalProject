if __name__ == "__main__":
    from rich.console import Console
    from models.board import Board
    board = Board.load_random_puzzle(difficulty=4)
    console = Console()
    console.print(board)
