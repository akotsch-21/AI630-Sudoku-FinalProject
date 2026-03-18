"""
Cage module defines the Cage class.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cell import Cell

class Cage:
    """
    Cage represents a group of cells, aka a "cage" in Killer Sudoku.
    This means that the cells in cage must sum to specific target_sum.
    """

    def __init__(self, cage_id: str, target_sum: int):
        """
        Initialize a Cage instance.

        Arguments:
            cage_id -- A unique identifier for the cage.
            target_sum -- The sum that the values in the cage must add up to.
        """
        self.cage_id = cage_id
        self.target_sum = target_sum
        self.cells = []

    def add_cell(self, cell: "Cell") -> None:
        """
        Add a cell to the cage.

        Arguments:
            cell -- The cell to add to the cage.
        """
        self.cells.append(cell)
