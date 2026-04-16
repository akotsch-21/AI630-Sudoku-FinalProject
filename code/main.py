if __name__ == "__main__":
    import time
    import copy
    from rich.live import Live
    from models.board import Board
    from models.backtracking import backtracking
    from models.backtracking import backtrackModified

    from models.backtracking import backtrackingWithForwardChecking
   
    board = Board.load_random_puzzle(difficulty=4)
    boardmod = copy.deepcopy(board)
    Fboard = copy.deepcopy(board)
    
    #print(f"Before revising {board}")
    # print(board)

    
    #print(f"Domains after revising {board}")
    # print(board)


    #board = backtracking(board, 0, 0)
    #print(f"After backtracking {board}")




with Live(board, refresh_per_second=20) as live:
    start = time.time()

    #print(cell.row, cell.col, cell.domains.intersection(cell.cage.getDomain()))

    correct, backtracks = backtracking(board, 0,0,0) # normal backtracking
    
    end = time.time()

    #live.update(board, refresh=True)
    print(f"Backtracking: Time taken: {end - start:.2f} seconds, Backtracking calls saved: {board.backtrack_calls-backtracks}")

with Live(boardmod, refresh_per_second=20) as live:
    start = time.time()

    #print(cell.row, cell.col, cell.domains.intersection(cell.cage.getDomain()))

    correct, backtracks = backtrackModified(boardmod, boardmod.select_unassigned_cell(),0) # normal backtracking
    
    end = time.time()

    #live.update(board, refresh=True)
    print(f"Backtracking Modified: Time taken: {end - start:.2f} seconds, Backtracking calls saved: {board.backtrack_calls-backtracks}")

"""
with Live(Fboard, refresh_per_second=20) as live:
    start = time.time()
    correct, backtracks = backtrackingWithForwardChecking(Fboard,Fboard.select_unassigned_cell(),0)
    end = time.time()

    print(f"Forward Checking: Time taken: {end - start:.2f} seconds, Backtracking calls saved: {board.backtrack_calls-backtracks}")
"""



#Gathering Times for benchmarking
"""timeBacktrack = []
timeBacktrackMod = []
backtracksSaved = []
n = 100
difficulty = 3
for i in range(n):
    
    
    board = Board.load_random_puzzle(difficulty=difficulty)
    boardmod = copy.deepcopy(board)

    requiredBacktrack = board.backtrack_calls
    print(f"\rpuzzle: {i+1} required backtracks {requiredBacktrack}\n","\033[A\033[A")
    

    start = time.time()
    correct, backtracks = backtracking(board, 0,0,0) # normal backtracking
    end = time.time()

    timeBacktrack.append(end-start)

    start = time.time()
    correct, backtracks = backtrackModified(boardmod, boardmod.select_unassigned_cell(),0) # modified backtracking
    end = time.time()

    backtracksSaved.append(requiredBacktrack-backtracks)
    timeBacktrackMod.append(end-start)



print(f" For {n} killer sudoku problems of difficulty {difficulty}:")
print(f" Average Time for Backtrack Modified: {sum(timeBacktrackMod)/n:.2f}\n",
      f"Average Time for Normal Backtrack  : {sum(timeBacktrack)/n:.2f}\n",
      f"Average Backtrack Saved            : {sum(backtracksSaved)/n}"
      )
"""