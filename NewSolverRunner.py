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

print(rowHints)
print(colHints)

grid = [[False for _ in range(len(colHints))] for _ in range(len(rowHints))]
colProgress = [0 for _ in colHints]

start = time.perf_counter()
solve(rowHints, colHints, colProgress, grid)
end = time.perf_counter()
dur = end - start
print(f"Solution took {dur:.6f} seconds.")
#Benchmark time: 72.754642
printGrid(grid)

#Largest ever solved: 45 x 45: https://www.nonograms.org/nonograms/i/84175
#Solution took 114285.677552 seconds (32 hours). Time taken is inflated since it includes time spent paused. Realistically more like 8 hours