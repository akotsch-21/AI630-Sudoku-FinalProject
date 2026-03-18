from models.cage import Cage
from models.cell import Cell
import random
import pandas as pd


class Board:
    MAX_LEN = 81
    PARQUET_PATH = "hf://datasets/jackcai1206/killer-sudoku-puzzles/data/train-00000-of-00001.parquet"

    @classmethod
    def load_random_puzzle(cls) -> "Board":
        # Load the puzzle
        df_sudoku = pd.read_parquet(cls.PARQUET_PATH)
        puzzle_strings = df_sudoku["puzzle_string"].to_list()
        difficulties = df_sudoku["difficulty"].to_list()

        # Select at random
        random_row = random.randint(0, len(puzzle_strings) - 1)
        puzzle_string = puzzle_strings[random_row]
        difficulty = difficulties[random_row]
        print(f"puzzle_string: {puzzle_string}")
        layout, sums_part = puzzle_string.split("\n", 1)
        print(f"layout: {layout}")
        print(f"sums_part: {sums_part}")

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
