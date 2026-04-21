"""
This modules defines the Board class, which represents a Killer Sudoku board.
"""

from models.cage import Cage
from models.cell import Cell
from models.dataset import ensure_local_parquet
from typing import Literal
from rich.table import Table
from rich.style import Style
from rich.text import Text
from rich import box
from rich.console import RenderResult
import randomcolor
import duckdb
from collections import deque
from copy import deepcopy
 

class Board:
    """
    Represents a Killer Sudoku board, which consists of a 9x9 grid of cells and a collection of cages.
    """

    def __init__(self, difficulty: Literal[2, 3, 4]):
        self.difficulty = difficulty
        self.cells = [[None for _ in range(9)] for _ in range(9)]
        self.cages = {} # cage_id: Cage
        self.arcs = {} # cell: set[neighboring cells]
        self.backtrack_calls = 0
        self.solved = False
        self.current_cell = None # Used for highlighting current cell being processed by UI

    def __rich_console__(self, _, __) -> RenderResult:
        main_table = Table(
            title=f"Killer Sudoku: Difficulty {self.difficulty}, Needed Backtrack Calls: {self.backtrack_calls}",
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
                        if cell == self.current_cell:
                            style = Style.combine([style, Style(color="cyan", bold=True, underline2=True)])

                        row_values.append(Text(val, style=style, justify="center"))
                    block_table.add_row(*row_values)

                block_row_tables.append(block_table)

            # Add the 3 blocks in this row to the main table
            main_table.add_row(*block_row_tables)

        yield main_table

    def __str__(self):
        result = f"Board(difficulty={self.difficulty})\n"
        result += "Cages:\n"
        for cage_id, cage in self.cages.items():
            result += f"  Cage {cage_id}: target_sum={cage.target_sum}, \
                cells={[(cell.row, cell.col) for cell in cage.cells]}\n"
        # result += "Arcs:\n"
        # for cell, neighbors in self.arcs.items():
        #     result += f"  Cell ({cell.row}, {cell.col}): {[f'({n.row}, {n.col})' for n in neighbors]}\n"

        result += "Cell Domains:\n"
        for row in self.cells:
            for cell in row:
                result += f"  Cell ({cell.row}, {cell.col}): {cell.domains}\n"

        result += "Cage Domains:\n"
        for cage_id, cage in self.cages.items():
            result += f"  Cage {cage_id}: {cage.domains}\n"

        result += "Board:\n"
        for row in self.cells:
            for cell in row:
                if cell.value is None:
                    result += ". "
                else:
                    result += f"{cell.value} "
            result += "\n"

        result += f"Total Cage Domains:{sum(len(cage.domains) for cage in self.cages.values())} total domains\n"
        result += f"Total Cell Domains:{sum(len(cell.domains) for row in self.cells for cell in row)} total domains\n"
        return result


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

        parquet_source = ensure_local_parquet()

        # Query a random row from the local parquet cache 
        # (was having some issues when training so just download it the full dataset and do it locally now).
        query = f"""
            SELECT puzzle_string, difficulty, num_cages,backtrack_calls
            FROM "{parquet_source}"
            {f"WHERE difficulty = {difficulty}" if difficulty is not None else ""}
            ORDER BY RANDOM()
            LIMIT 1
        """

        puzzle_string, difficulty, num_cages,backtrack_calls = duckdb.query(query).fetchone()
        return cls.from_puzzle_string(puzzle_string, difficulty=difficulty, num_cages=num_cages, backtrack_calls=backtrack_calls)

    @classmethod
    def from_puzzle_string(
        cls,
        puzzle_string: str,
        difficulty: int,
        num_cages: int | None = None,
        backtrack_calls: int | None = None
    ) -> "Board":
        """
        Construct a board directly from a puzzle string.

        Arguments:
            puzzle_string -- Board layout and cage sums in the dataset format.
            difficulty -- Difficulty to assign to this board.

        Returns:
            Board: A populated board instance.
        """
        layout, sums_part = puzzle_string.split("\n", 1)
        cage_entries = [entry for entry in sums_part.split(";") if entry]

        # Create randomly pleasing colors for the cages
        # @see https://github.com/kevinwuhoo/randomcolor-py/blob/4b05e3aa2bbf6cd387d3c24e2a37fffd241a6cdb/randomcolor/__init__.py#L103
        cage_count = int(num_cages) if num_cages is not None else len(cage_entries)
        cage_colors = randomcolor.RandomColor().generate(count=cage_count, format_="rgb Array")

        board = Board(difficulty=difficulty)
        board.backtrack_calls = int(backtrack_calls) if backtrack_calls is not None else 0

        for entry in cage_entries:
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
        self.cells = [[None for _ in range(9)] for _ in range(9)]
        for cage in self.cages.values():
            for cell in cage.cells:
                self.cells[cell.row][cell.col] = cell
            cage.build_domains()

        self.arcs =self._build_arcs()

    def revise_arcs(self) -> int:
        """
        Revise the board arcs.
        """
        queue = deque()
        count = 0
        # Add all arcs to queue. (cell: neighbor)
        for cell, neighbors in self.arcs.items():
            for neighbor in neighbors:
                queue.append((cell, neighbor))

        while queue:
            cell, neighbor = queue.popleft()
            if self._revise(cell, neighbor):

                # Sanity check: If empty puzzle is not possible bc dataset only has solvable puzzles
                if not cell.domains:
                    print("No solution possible -- Bug?")
                    return

                # If there was a change, we'll need to backtrack and check all neighbors again
                for other_neighbor in self.arcs[cell]:
                    if other_neighbor != neighbor:
                        queue.append((other_neighbor, cell))
                count+=1
        return count
                

    def iter_cells(self) -> list[Cell]:
        """
        Return all board cells in row-major order.
        """
        return [cell for row in self.cells for cell in row]

    def is_solved(self) -> bool:
        """
        Return True when every cell is assigned.
        """
        return all(cell.value is not None for cell in self.iter_cells())

    def select_unassigned_cell(self) -> Cell | None:
        """
        Select an unassigned cell using a minimum remaining values heuristic.
        """
        unassigned = [cell for cell in self.iter_cells() if cell.value is None]
        if not unassigned:
            return None
        return min(unassigned, key=lambda cell: (len(cell.domains.intersection(cell.cage.getDomain())), cell.row, cell.col))
    
    def findLCS(self,cell):
        lcs = []
        r = cell.row
        c = cell.col
        for val in cell.domains.intersection(cell.cage.getDomain()):
            lcsBoard= deepcopy(self)
            lcsBoard.cells[r][c].value = val
            lcs.append([lcsBoard.revise_arcs(),val])
        
        
        return lcs
        
    def is_valid(self, cell: Cell, value: int | None = None) -> bool:
        """
        Check whether assigning a value to a cell is consistent with board constraints.
        If value is omitted, the cell's current value is validated.
        """
        if value is None:
            if cell.value is None:
                return True
            value = cell.value

        # Row/column/box/cage all-different is encoded by peers in arcs.
        for peer in self.arcs.get(cell, set()):
            if peer.value == value and peer != cell:
                return False

        cage = cell.cage
        if cage is None:
            return True

        assigned_values = []
        for cage_cell in cage.cells:
            if cage_cell == cell:
                continue

            if cage_cell.value is not None:
                if cage_cell.value == value:
                    return False
                assigned_values.append(cage_cell.value)

        current_sum = sum(assigned_values) + value
        remaining_slots = sum(1 for cage_cell in cage.cells if cage_cell != cell and cage_cell.value is None)

        if current_sum > cage.target_sum:
            return False

        if remaining_slots == 0:
            return current_sum == cage.target_sum

        used_digits = set(assigned_values)
        used_digits.add(value)
        available_digits = sorted(digit for digit in range(1, 10) if digit not in used_digits)

        if len(available_digits) < remaining_slots:
            return False

        min_remaining_sum = sum(available_digits[:remaining_slots])
        max_remaining_sum = sum(available_digits[-remaining_slots:])
        remaining_sum_needed = cage.target_sum - current_sum
        return min_remaining_sum <= remaining_sum_needed <= max_remaining_sum

    def propagate_constraints(self) -> bool:
        """
        Recompute domains from the current partial assignment until a fixed point.
        Returns False if any domain becomes empty or a contradiction is found.
        """
        changed = True

        while changed:
            changed = False
            for cell in self.iter_cells():
                if cell.value is not None:
                    if not self.is_valid(cell):
                        return False
                    cell.domains = {cell.value}
                    continue

                valid_domain = {candidate for candidate in cell.domains if self.is_valid(cell, candidate)}
                if not valid_domain:
                    return False

                if valid_domain != cell.domains:
                    cell.domains = valid_domain
                    changed = True

                if len(cell.domains) == 1 and cell.value is None:
                    cell.value = next(iter(cell.domains))
                    changed = True

        self.solved = self.is_solved()
        return True

    def _revise(self, cell: Cell, neighbor: Cell) -> bool:
        """
        Revise the domain of the given cell based on its neighbors.
        Arguments:
            cell -- The cell to revise.
            neighbor -- The neighboring cell for the current arc.

        Returns:
            True if the domain of the cell was revised, False otherwise.
        """
        self.current_cell = cell
        revised = False
        delete_domain_values = set()
        for cell_domain in cell.domains:
            # If there are no values different, we can remove from the domain of cell.
            # Constraint is difference for neighbors in rows, cols and 3x3 grid.
            # ie: { 1, 2 } -> { 1 } if neighbor domain is { 1 }
            if not any(cell_domain != neighbor_domain for neighbor_domain in neighbor.domains):
                delete_domain_values.add(cell_domain)

            if cell.cage is not None and neighbor.cage is not None and cell.cage == neighbor.cage:
                # If there are no values that can sum up to target sum, we can remove from the domain of cell.
                # ie: { (1, 2), (2, 3) } -> { (1, 2) } if neighbor domain is { (2, 3) } and target sum is 3
                cage = cell.cage

                # We are checking cage constraints here
                # For each domain of the cell, we need to check if there is a corresponding
                # domain in the neighbor that also exists in the cage domains and sums up to
                # the cages target sum.
                if not any(cell_domain in cage_domain
                           and neighbor_domain in cage_domain
                           and sum(cage_domain) == cage.target_sum
                           and cell_domain != neighbor_domain
                           for cage_domain in cage.domains for neighbor_domain in neighbor.domains):
                    delete_domain_values.add(cell_domain)

        if delete_domain_values:
            cell.domains -= delete_domain_values
            revised = True
            if len(cell.domains) == 1:
                cell.value = next(iter(cell.domains))

        return revised

    def _build_arcs(self) -> dict[Cell, set[Cell]]:
        """
        Build a map of each cell to its neighboring cell. These are:
            - Cells in the same row
            - Cells in the same column
            - Cells in the same box (3x3 subgrid)
            - Cells in the same cage
        Returns:
            A dictionary mapping each cell to a set of its neighboring cells.
        """
        _arcs = {}

        for row in self.cells:
            for cell in row:
                _arcs[cell] = set()
                # Rows constraint
                for col in range(9):
                    if self.cells[cell.row][col] != cell:
                        _arcs[cell].add(self.cells[cell.row][col])
                # Columns constraint
                for r2 in range(9):
                    if self.cells[r2][cell.col] != cell:
                        _arcs[cell].add(self.cells[r2][cell.col])

                # 3x3 box constraint
                box_r_start = (cell.row // 3) * 3
                box_c_start = (cell.col // 3) * 3

                for r in range(box_r_start, box_r_start + 3):
                    for c in range(box_c_start, box_c_start + 3):
                        if self.cells[r][c] != cell:
                            _arcs[cell].add(self.cells[r][c])

        # Add cage arcs
        cage_arcs = self._build_cage_arcs()
        for cell, neighbors in cage_arcs.items():
            # Add potentially missing arcs from cages
            if cell in _arcs:
                _arcs[cell].update(neighbors)
            # Otherwise, arcs are whatever the cages can support
            else:
                _arcs[cell] = neighbors

        return _arcs

    def _build_cage_arcs(self) -> dict[Cell, set[Cell]]:
        """
        Build arcs for cells in the same cage.
        Returns:
            A dictionary mapping each cell to a set of its neighboring cells in the same cage.
        """
        _arcs = {}

        for cage in self.cages.values():
            for cell in cage.cells:
                if cell not in _arcs:
                    _arcs[cell] = set()

                for other_cell in cage.cells:
                    if other_cell != cell:
                        _arcs[cell].add(other_cell)

        return _arcs
