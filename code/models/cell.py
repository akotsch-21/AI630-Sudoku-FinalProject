"""
Cell module defines the Cell class.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from cage import Cage

class Cell:
    """
    Cell represents a single cell in a Killer Sudoku board.
    """

    def __init__(self, row: int, col: int, cage: Optional["Cage"] = None):
        """
        Initialize a Cell instance.

        Arguments:
            row -- The row index of the cell.
            col -- The column index of the cell.
            cage -- The cage to which the cell belongs (optional).
        """
        self.row = row
        self.col = col
        self.cage = cage
        self.value = None
        self.domains = set(range(1, 10))

    def __lt__(self, other: "Cell") -> bool:
        if self.row == other.row:
            return self.col < other.col
        return self.row < other.row

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return False

        return self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        return hash((self.row, self.col))

    def reset(self):
        """
        Reset the cell's value and domains.
        """
        self.value = None
        self.domains = set(range(1, 10))