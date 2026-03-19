
def backtraking(board,domain):
    for i in range(9):
        for j in range(9):
            num = int(input())
            print(i,j)
            board.cells[i][j].value = num 
            print(board.is_valid(board.cells[i][j]))
            print(board)
        