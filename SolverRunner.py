from Solver import *
from Scrapers import *
import time

site = "nonograms.org"

rowHints = []
colHints = []

url = input(f"Enter the URL to the puzzle from {site}: ")

match site:
    case "nonograms.org":
        rowHints, colHints = puzzle_nonograms_getHints(url)
    case "puzzle-nonograms.com":
        rowHints, colHints = nonograms_org_getHints(url)
    case _:
        raise Exception(f"Invalid site {site}")

grid = [[False for _ in range(len(colHints))] for _ in range(len(rowHints))]
colProgress = [[0] for _ in colHints]

start = time.perf_counter()

backtrackSolve(rowHints, colHints, colProgress, grid, 0, 0, 0)
end = time.perf_counter()
dur = end - start
print(f"Solution took {dur:.6f} seconds.")
printGrid(grid)