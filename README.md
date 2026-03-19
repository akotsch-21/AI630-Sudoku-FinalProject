# AI630-Sudoku-FinalProject

## Abstract
Sudoku is a centuries old game involving logic and very little mental arithmetics. We aim to make it more challenging by introducing additional custom rules that change the game into what is known as "Killer Sudoku".

We will build an AI Agent that will be able to play this more complex version of Sudoku and attempt win in the most optimal way. The states will be the progression of the puzzle as the algorithm fills in more squares. The initial state will be the numbers that are initially filled in and the sum boxes for the killer sudoku variation. The operators will be to fill in and delete a number between 1 and 9 in any of the unfilled starting squares. The goal will be a filled puzzle that follows the preset rules of killer sudoku. The path cost will be the sum of each filling and deletion of a number to reach the goal.

## Developers
- Aidan Kotsch
- Carter Ptak
- Jean Luis Urena

## Repository Structure
- `code/`: Implementation/models/scripts/etc.
- `resources/`: Research papers, examples, reference links, notes that we used for the project, and the final presentation slides. .
- `data/`: Datasets

## How To Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run main.py:
   ```bash
   python code/main.py
   ```
