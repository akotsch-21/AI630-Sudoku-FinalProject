import copy
import time


from rich import cells
from rich.live import Live
from models.board import Board

def backtracking(board,row, col,count):
    count += 1

    #check if we have reached the end of the board and if it is solved
    if row == 8 and col == 9 and board.is_solved():
        return True, count
    
    #move down a row once one is complete
    if col == 9:
        row += 1
        col = 0

    #retrieve the domain of the current cell
    domain = board.cells[row][col].domains

    # if the cell is already filled, move to the next one
    if board.cells[row][col].value is not None:
        return backtracking(board, row, col+1, count)
    
    #iterate through the domain of the current cell and try to assign a value
    for value in domain:
        board.cells[row][col].value = value
        if board.is_valid(board.cells[row][col]):
            #if value is valid, move to the next cell
            
            found, count = backtracking(board, row, col+1, count)

            if found:
                return True, count
            
        #if value is not valid, reset the cell and try the next value in the domain
        board.cells[row][col].value = None

    return False, count


def backtrackingWithAC3(board,row, col,count):
    count += 1
    board.revise_arcs()

    #check if we have reached the end of the board and if it is solved
    if row == 8 and col == 9 and board.is_solved():
        return True, count
    
    #move down a row once one is complete
    if col == 9:
        row += 1
        col = 0

    #retrieve the domain of the current cell
    domain = board.cells[row][col].domains

    # if the cell is already filled, move to the next one
    if board.cells[row][col].value is not None:
        return backtrackingWithAC3(board, row, col+1, count)
    
    #iterate through the domain of the current cell and try to assign a value
    for value in domain:
        board.cells[row][col].value = value
        if board.is_valid(board.cells[row][col]):
            #if value is valid, move to the next cell
            
            found, count = backtrackingWithAC3(board, row, col+1, count)

            if found:
                return True, count
            
        #if value is not valid, reset the cell and try the next value in the domain
        board.cells[row][col].value = None

    return False, count

def backtrackModified(board,cell,count):
     #This backtracking version has arc revision, MRV heuristic, and LCS heuristic
    count +=1
    board.revise_arcs()
    #print(f"Backtracking call count: {count}")

    #check if we have reached the end of the board and if it is solved
    if board.is_solved():
        return True, count
    domain  = cell.domains.intersection(cell.cage.getDomain())
    

    if len(domain)==1: 
        cell.value = list(domain)[0]
        if board.is_valid(cell):
            #if value is valid, move  to the next cell
            #revise domains
            found, count = backtrackModified(board,board.select_unassigned_cell(), count)

            if found:
                return True, count
            
    else:
        found, count = backtracking(board,0,0, count)
        if found:
            return True, count

    return False, count

def backtrackingWithForwardChecking(board,cell,count):
    #This backtracking version has arc revision, MRV heuristic, and LCS heuristic
    count +=1
    board.revise_arcs()
    #print(count)
    #print(f"Backtracking call count: {count}")

    #check if we have reached the end of the board and if it is solved
    if board.is_solved():
        return True, count
    lcsValues = board.findLCS(cell)
    lcsValues.sort() # sort values by least constraining 
    #iterate through the domain of the current cell and try to assign a value
    for value in lcsValues:
        cell.value = value[1]
        if board.is_valid(cell):
            #if value is valid, move  to the next cell
            #revise domains
            found, count = backtrackingWithForwardChecking(board,board.select_unassigned_cell(), count)

            if found:
                return True, count
            
        cell.value = None

    return False, count


