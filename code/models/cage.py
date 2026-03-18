class Cage:
    def __init__(self, cage_id: str, target_sum: int):
        self.cage_id = cage_id
        self.target_sum = target_sum
        self.cells = []

    def add_cell(self, cell):
        self.cells.append(cell)