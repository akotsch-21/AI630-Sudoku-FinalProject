class Cell:
    def __init__(self, row: int, col: int, cage = None):
        self.row = row
        self.col = col
        self.cage = cage
        self.value = None
