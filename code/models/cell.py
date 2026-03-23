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
