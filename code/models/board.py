from models.cage import Cage
from models.cell import Cell
import random
import requests


class Board:
    MAX_LEN = 81
    MAX_PUZZLE_ROWS = 960 # As per HuggingFace dataset info.
    PUZZLE_URI = "https://datasets-server.huggingface.co/rows?dataset=jackcai1206%2Fkiller-sudoku-puzzles&config=default&split=train"

    @classmethod
    def load_random_puzzle(cls) -> "Board":
        """
        Load a random puzzle from the parquet file and construct the sudoku Board object.

        Returns:
            Board: A Board object representing the loaded puzzle.
        """

        # Download a random row from hugging face.
        random_row = random.randint(0, cls.MAX_PUZZLE_ROWS - 1)
        response = requests.get(url = cls.PUZZLE_URI + f"&offset={random_row}&length=1", timeout=10)
        data = response.json()
        row = data["rows"][0]["row"]
        puzzle_string = row["puzzle_string"]
        difficulty = row["difficulty"] # We're always just pulling one row, so take first.

        layout, sums_part = puzzle_string.split("\n", 1)

        if len(layout) != cls.MAX_LEN:
            raise ValueError(f"Invalid puzzle string: {puzzle_string}")

        board = Board(difficulty=difficulty)

        for entry in sums_part.split(";"):
            cage_id, target_sum = entry.split(":")
            cage = Cage(cage_id, int(target_sum))
            board.add_cage(cage)

        for i, cage_id in enumerate(layout):
            row = i // 9
            col = i % 9

            cage = board.get_cage_by_id(cage_id)
            if cage is None:
                raise ValueError(f"Invalid cage id: {cage_id}")

            cell = Cell(row, col, cage)
            cage.add_cell(cell)

        board.reload_cells()
        return board

    def __init__(self, difficulty: str):
        self.difficulty = difficulty
        self.cells = [[None for _ in range(9)] for _ in range(9)]
        self.cages = {}

    def add_cage(self, cage: Cage):
        self.cages[cage.cage_id] = cage

    def get_cage_by_id(self, cage_id: str) -> Cage:
        return self.cages[cage_id]

    def reload_cells(self):
        for cage in self.cages.values():
            for cell in cage.cells:
                self.cells[cell.row][cell.col] = cell

    def __str__(self):
        result = f"Board(difficulty={self.difficulty})\n"
        result += "Cages:\n"
        for cage_id, cage in self.cages.items():
            result += f"  Cage {cage_id}: target_sum={cage.target_sum}, cells={[(cell.row, cell.col) for cell in cage.cells]}\n"
        result += "Cells:\n"
        for row in self.cells:
            for cell in row:
                if cell.value is None:
                    result += ". "
                else:
                    result += f"{cell.value} "
            result += "\n"
        return result
