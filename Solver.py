def printGrid(grid, rowHints = None, colHints = None, stop = -1):
    if (not rowHints == None): print(rowHints)
    if (not colHints == None): print(colHints)
    for i, r in enumerate(grid):
        for cell in r:
            #"⯀□"
            print("■" if cell else "□", end=" ")
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
def backtrackSolve(rowHints, colHints, colProgress, grid, hintIndex, r, c):
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
            #If the grid is filled in at this square
            if (grid[r][i]):
                #If we already have too many column units, fail
                if (len(colProgress[i]) > len(colHints[i])): return False
                #If adding this square exceeded the limit for the current column hint, fail
                if (colProgress[i][-1]+1 > colHints[i][len(colProgress[i])-1]): return False
            else:
                #The grid is not filled in at this square
                #If excluding this square cuts off the current unit at the wrong length, fail
                if (colProgress[i][-1] != 0 and colProgress[i][-1] != colHints[i][len(colProgress[i])-1]): return False
        #We have not failed yet.
        #Update colProgress
        for i in range(len(colHints)):
            #If the grid is filled in at this square, increment the current colProgress
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
        #Move the unit forwards
        grid[r][c] = False
        grid[r][c+unitLen] = True
        c += 1
    #Nothing worked. Backtrack
    if newRow:
        #Restore the previous colProgress
        for i in range(len(colHints)):
            if (colProgress[i][-1] != 0): colProgress[i][-1] -= 1
            if (colProgress[i][-1] == 0 and r > 1 and grid[r-2][i]): colProgress[i].pop()
    return False