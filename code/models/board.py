"""
This modules defines the Board class, which represents a Killer Sudoku board.
"""

from models.cage import Cage
from models.cell import Cell
from typing import Literal
import duckdb


class Board:
    """
    Represents a Killer Sudoku board, which consists of a 9x9 grid of cells and a collection of cages.
    """
    MAX_LEN = 81

    # Get the parquet file path with:
    # curl -X GET \
    #  "https://huggingface.co/api/datasets/jackcai1206/killer-sudoku-puzzles/parquet/default/train"
    PUZZLE_PARQUET = "https://huggingface.co/api/datasets/jackcai1206/killer-sudoku-puzzles/parquet/default/train/0.parquet"

    @classmethod
    def load_random_puzzle(cls, difficulty: Literal[2, 3, 4] | None = None) -> "Board":
        """
        Load a random puzzle from the parquet file and construct the sudoku Board object.

        Arguments:
            difficulty -- The difficulty level of the puzzle to load (2, 3, or 4).
                          If None, a random difficulty will be selected.

        Returns:
            Board: A Board object representing the loaded puzzle.
        """

        # Download a random row from hugging face using DuckDB's parquet reader.
        query = f"""
            SELECT puzzle_string, difficulty
            FROM "{cls.PUZZLE_PARQUET}"
            {f"WHERE difficulty = {difficulty}" if difficulty is not None else ""}
            ORDER BY RANDOM()
            LIMIT 1
        """

        puzzle_string, difficulty = duckdb.query(query).fetchone()
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

    def __init__(self, difficulty: Literal[2, 3, 4]):
        self.difficulty = difficulty
        self.cells = [[None for _ in range(9)] for _ in range(9)]
        self.cages = {}

    def add_cage(self, cage: Cage) -> None:
        """
        Add a cage to the board.

        Arguments:
            cage -- The cage to add to the board.
        """
        self.cages[cage.cage_id] = cage

    def get_cage_by_id(self, cage_id: str) -> Cage | None:
        """
        Get a cage by its ID.
        Arguments:
            cage_id -- The ID of the cage to retrieve.

        Returns:
            The cage with the specified ID, or None if no such cage exists.
        """
        return self.cages.get(cage_id)

    def reload_cells(self):
        """
        References cells from cages into the main board structure.
        """
        for cage in self.cages.values():
            for cell in cage.cells:
                self.cells[cell.row][cell.col] = cell

    def __str__(self):
        result = f"Board(difficulty={self.difficulty})\n"
        result += "Cages:\n"
        for cage_id, cage in self.cages.items():
            result += f"  Cage {cage_id}: target_sum={cage.target_sum}, \
                cells={[(cell.row, cell.col) for cell in cage.cells]}\n"
        result += "Cells:\n"
        for row in self.cells:
            for cell in row:
                if cell.value is None:
                    result += ". "
                else:
                    result += f"{cell.value} "
            result += "\n"
        return result
    
    def is_valid(self,cell):
        """
        check if board is in a valid state after input of cell
        """
        row = cell.row
        col = cell.col
        val = cell.value

        box = ((row//3)*3, (col//3)*3)

        #* check row and collumn for repeat values 
        for i in range(9):
            if self.cells[row][i].value == val and col != i:
                print("column")
                return False
            if self.cells[i][col].value == val and row != i:
                print("row")
                return False
        
        #* check box 
        for i in range(box[0],box[0]+3):
            for j in range(box[1], box[1]+3):
                if self.cells[i][j].value == val and row != i and col != j:
                    print("box")
                    return False
        

        #* check cages
        for cage in self.cages.values():
            if cage.in_cage(cell):
                print("cage")
                return cage.is_valid()
        
        return True
        
        
