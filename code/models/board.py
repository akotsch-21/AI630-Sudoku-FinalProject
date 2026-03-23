"""
This modules defines the Board class, which represents a Killer Sudoku board.
"""

from models.cage import Cage
from models.cell import Cell
from typing import Literal
from rich.table import Table
from rich.style import Style
from rich.text import Text
from rich import box
from rich.console import Console, ConsoleOptions, RenderResult
import randomcolor
import duckdb


class Board:
    """
    Represents a Killer Sudoku board, which consists of a 9x9 grid of cells and a collection of cages.
    """

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
            SELECT puzzle_string, difficulty, num_cages
            FROM "{cls.PUZZLE_PARQUET}"
            {f"WHERE difficulty = {difficulty}" if difficulty is not None else ""}
            ORDER BY RANDOM()
            LIMIT 1
        """

        puzzle_string, difficulty, num_cages = duckdb.query(query).fetchone()
        layout, sums_part = puzzle_string.split("\n", 1)
        # Create randomly pleasing colors for the cages
        # @see https://github.com/kevinwuhoo/randomcolor-py/blob/4b05e3aa2bbf6cd387d3c24e2a37fffd241a6cdb/randomcolor/__init__.py#L103
        cage_colors = randomcolor.RandomColor().generate(count=num_cages, format_="rgb Array")

        board = Board(difficulty=difficulty)

        for entry in sums_part.split(";"):
            cage_id, target_sum = entry.split(":")
            cage = Cage(cage_id, int(target_sum), cage_colors.pop())
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

    def generate_table(self, current_pos: tuple[int, int] | None = None) -> Table:
        """
        Get a string representation of the board, showing the current values of the cells.

        Arguments:
            current_pos -- The current position used to highlight the cell being processed.
        """

        main_table = Table(
            title="Killer Sudoku",
            title_justify="center",
            expand=True,
            show_header=False,
            show_footer=False,
            box=box.SQUARE,
            padding=(0, 0),
            pad_edge=False
        )

        # 3x block rows, top, middle and bottom
        for block_row in range(3):
            block_row_tables = []

            # 3x block columns, left, right and middle
            for block_col in range(3):
                block_table = Table(show_header=False, show_footer=False,expand=True, padding=(0, 0), box=box.HORIZONTALS, pad_edge=False)

                # row within the block
                for r in range(3):
                    row_values = []
                    for c in range(3):
                        cell_row = block_row * 3 + r
                        cell_col = block_col * 3 + c
                        cell = self.cells[cell_row][cell_col]

                        val = str(cell.value) if cell.value is not None else "."

                        # Only cells with cages get background colors to identify cage.
                        if cell.cage is not None:
                            style = Style(bgcolor=cell.cage.color)
                        else:
                            style = Style()

                        # Highlight the current cell being processed
                        if (cell_row, cell_col) == current_pos:
                            style = Style.combine([style, Style(color="cyan", bold=True, underline2=True)])

                        row_values.append(Text(val, style=style, justify="center"))
                    block_table.add_row(*row_values)

                block_row_tables.append(block_table)

            # Add the 3 blocks in this row to the main table
            main_table.add_row(*block_row_tables)

        return main_table

    def __rich_console__(self, _, __) -> RenderResult:
        yield self.generate_table()

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
        
        
