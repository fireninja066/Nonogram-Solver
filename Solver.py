import time

def printGrid(grid, rowHints = None, colHints = None, stop = -1):
    if (not rowHints == None): print(rowHints)
    if (not colHints == None): print(colHints)
    for i, r in enumerate(grid):
        for cell in r:
            #"On mac: ⯀□"
            print("■" if cell > 0 else "□", end=" ")
        print()
        if (i == stop):
            break

def generateHints(grid):
    rowHints = []
    colHints = []
    for r in range(len(grid)):
        rowHint = []
        rowUnit = False
        for c in range(len(grid[0])):
            if rowUnit:
                if grid[r][c]:
                    rowHint[-1] += 1
                else:
                    rowUnit = False
            else:
                if grid[r][c]:
                    rowHint.append(1)
                    rowUnit = True
        rowHints.append(rowHint)
    for c in range(len(grid[0])):
        colHint = []
        colUnit = False
        for r in range(len(grid)):
            if colUnit:
                if grid[r][c]:
                    colHint[-1] += 1
                else:
                    colUnit = False
            else:
                if grid[r][c]:
                    colHint.append(1)
                    colUnit = True
        colHints.append(colHint)
    return rowHints, colHints

iters = 0
def backtrackSolve(rowHints, colHints, colProgress, grid, hintIndex = 0, r = 0, c = 0):
    global iters
    if (iters >= 10000000):
        iters = 0
        printGrid(grid, stop = r)
        print("\n\n")
    iters += 1
    #printGrid(grid)
    #input()
    #Initiate newRow variable
    newRow = False
    #If we are out of hints for this row, check the whole row
    if (hintIndex >= len(rowHints[r])):
        #For each column
        for i in range(len(colHints)):
            #If the grid is filled in at this cell
            if (grid[r][i]):
                #If we already have too many column units, fail
                if (len(colProgress[i]) > len(colHints[i])): return False
                #If filling this cell exceeded the limit for the current column hint, fail
                if (colProgress[i][-1]+1 > colHints[i][len(colProgress[i])-1]): return False
            else:
                #The grid is not filled in at this cell
                #If excluding this cell cuts off the current unit at the wrong length, fail
                if (colProgress[i][-1] != 0 and colProgress[i][-1] != colHints[i][len(colProgress[i])-1]): return False
        #We have not failed yet.
        #Update colProgress
        for i in range(len(colHints)):
            #If the grid is filled in at this cell, increment the current colProgress
            if (grid[r][i]): colProgress[i][-1] += 1
            elif (colProgress[i][-1] != 0): colProgress[i].append(0)
        #Increment r and reset hintIndex and c
        r += 1
        c = 0
        hintIndex = 0
        newRow = True
    #If r >= the number of rows, then we have found the solution
    if (r >= len(rowHints)): return True
    unitLen = rowHints[r][hintIndex]
    #If c + the length of this unit > the number of columns, then we have failed
    if (c + unitLen > len(colHints)): return False
    #Set up first placement
    for i in range(unitLen): grid[r][c+i] = True
    #Attempt each possible placement
    while (True):
        #If we've found a successful path, return True
        if backtrackSolve(rowHints, colHints, colProgress, grid, hintIndex+1, r, c+unitLen+1): return True
        #If we've run out of possible placements for this unit
        if (c+unitLen+1 > len(colHints)):
            #Remove this unit from the grid
            for i in range(unitLen): grid[r][c+i] = False
            #Exit the loop
            break
        #Move the unit forwards one unit
        grid[r][c] = False
        grid[r][c+unitLen] = True
        c += 1
    if newRow:
        #Restore the previous colProgress
        for i in range(len(colHints)):
            if (colProgress[i][-1] != 0): colProgress[i][-1] -= 1
            if (colProgress[i][-1] == 0 and r > 1 and grid[r-2][i]): colProgress[i].pop()
    if r == 0 and c == 0: print("No solution found")
    return False

"""
New solver code ------------------------------------------------------------------------------------------------------------
"""        

def readPermutation(spaces, rowHint, rowLength):
    hintIndex = 0
    i = 0
    while i < rowLength:
        if hintIndex >= len(rowHint):
            yield -1
            i += 1
            continue
        for _ in range(spaces[hintIndex]):
            yield -1
            i += 1
        for _ in range(rowHint[hintIndex]):
            yield 1
            i += 1
        hintIndex += 1

def generateValidRowPermutations(r, rowHint, grid):
    cur = [1 for _ in rowHint]
    cur[0] = 0
    rowLength = len(grid[0])
    filledCells = sum(rowHint)
    emptyCells = rowLength - filledCells
    moveableSpace = rowLength - (filledCells + len(rowHint) - 1)
    while cur[0] <= moveableSpace:
        perm = readPermutation(cur, rowHint, rowLength)
        #Check if the permutation is valid
        c = 0
        while c < rowLength:
            cell = next(perm)
            if cell == -1 and grid[r][c] > 0:
                break
            elif cell > 0 and grid[r][c] == -1:
                break
            c += 1
        else:
            #The permutation is valid. Yield it
            yield readPermutation(cur, rowHint, rowLength)
        #Increment the permutation
        for i in range(len(cur) - 1, -1, -1):
            cur[i] += 1
            if sum(cur) <= emptyCells:
                break
            elif i == 0:
                break
            cur[i] = 1

def buildDownwardsThenUndo(r, colProgress, colHints, grid):
    rowLength = len(grid[0])
    built = [0 for i in range(rowLength)]
    failed = False
    for c in range(rowLength):
        if grid[r][c] == 1:
            built[c] = colHints[c][colProgress[c]]
            for i in range(colHints[c][colProgress[c]]):
                try:
                    grid[r+i][c] += 1
                except IndexError:
                    failed = True
                    break
            if failed: break
            i += 1
            if r + i < len(grid):
                grid[r+i][c] = -1
            colProgress[c] += 1
            if colProgress[c] >= len(colHints[c]):
                for j in range(r + i + 1, len(grid)):
                    grid[j][c] = -1
    yield not failed
    failed = False
    for c in range(rowLength):
        if built[c] > 0:
            for i in range(built[c]):
                try:
                    grid[r+i][c] -= 1
                except IndexError:
                    failed = True
                    break
            if failed: break
            i += 1
            if r + i < len(grid):
                grid[r+i][c] = 0
            if colProgress[c] >= len(colHints[c]):
                for j in range(r + i + 1, len(grid)):
                    grid[j][c] = 0
            colProgress[c] -= 1
    yield

def buildPermutationThenUndo(r, perm, grid):
    #Precondition: Perm is guaranteed to be a valid permutation
    edits = []
    while True:
        try:
            tile = next(perm)
        except StopIteration: break
        edits.append(tile)
    for c in range(len(grid[0])):
        grid[r][c] += edits[c]
    yield
    for c in range(len(grid[0])):
        grid[r][c] -= edits[c]
    yield

printTime = -1
def solve(rowHints, colHints, colProgress, grid, r = 0):
    """
    global printTime
    if r == 0: printTime = time.perf_counter()
    
    if time.perf_counter() > printTime:
        printGrid(grid, stop = r)
        print("\n\n")
        printTime += 5
    """
    if r >= len(rowHints): return True
    permutations = generateValidRowPermutations(r, rowHints[r], grid)
    while True:
        try:
            cand = next(permutations)
        except StopIteration: break
        step1 = buildPermutationThenUndo(r, cand, grid)
        step2 = buildDownwardsThenUndo(r, colProgress, colHints, grid)
        next(step1)
        if next(step2): #Building downwards may reject some permutations
            if solve(rowHints, colHints, colProgress, grid, r + 1): return True
        next(step2)
        next(step1)
    return False