#python -u "c:\Users\zacar\Documents\GitHub\Nonogram Solver\CrossSolver.py"

import inspect

from Solver import *
from Scrapers import *
import time
import itertools

DEBUG = False
iters = 0
chars = "✕✕□◧■"#"✕✕□■■"
permProg = 0
numPerms = 0

def debug(*args, **kwargs):
    global DEBUG
    if DEBUG:
        print(*args, **kwargs)
        waitForInput()

def waitForInput():
    if DEBUG:
        _ = input()

class GridCell:
    """
    Default value 0.
    Supports comparisons with integer values.
    \nKey:\n
    -2: This cell must be empty; two units have specified this cell as empty\n
    -1: This cell must be empty\n
    0: We have no information about this cell\n
    1: One fiber has placed a unit occupying this cell\n
    2: Two fibers have placed units occupying this cell\n
    After a valid cross permutation is selected and units are placed inwards, all cells within it must hold either -1 or 2
    """
    def __init__(self):
        self.val = 0

    def __eq__(self, other):
        return self.val == other

    def __lt__(self, other):
        return self.val < other

    def __gt__(self, other):
        return self.val > other

    def __le__(self, other):
        return self.val <= other

    def __ge__(self, other):
        return self.val >= other
    
    def __iadd__(self, amount):
        self.val += amount
        return self

    def __add__(self, amount):
        return self.val + amount

    def __isub__(self, amount):
        self.val -= amount
        return self

    def __str__(self):
        return str(self.val)

class Hint:
    """
    Wrapper around a list of integers representing desired unit lengths along a fiber.
    """
    def __init__(self, hint: list[int]):
        self.hint = hint
        self.prog = 0

    def __iadd__(self, val):
        self.prog += val
        if (self.prog > len(self.hint)):
            raise Exception("Hint progress has been excessively increased")
        return self

    def __isub__(self, val):
        self.prog -= val
        if (self.prog < 0):
            raise Exception("Hint progress decreased below 0")
        return self

    def __len__(self):
        """
        Length is determined as len(hint) - prog
        """
        return len(self.hint) - self.prog

    def __getitem__(self, i):
        """
        Index is relative to prog
        """
        return self.hint[self.prog + i]

    def __iter__(self):
        return iter(self.hint[self.prog:])

    def isComplete(self):
        return len(self) == 0

    def view(self):
        return self.hint[self.prog]

    def take(self):
        self.prog += 1
        return self.hint[self.prog - 1]

    def restore(self):
        self.prog -= 1
        return self.hint[self.prog]

class Fiber:
    """
    A row or column within the grid, with special focus on the elements near the end which have not been permuted yet.
    """
    def __init__(self, cellList: list[GridCell], hint: Hint, tag):
        self.cellList = cellList
        self.length = len(cellList)
        self.prog = 0
        self.hint = hint
        self.progHistory = []
        self.unitLocations = []
        self.tag = tag

    def __iadd__(self, dist):
        """
        Inserts the current unit at the specified distance away from prog.
        Adds the unit's location to unitLocations and the prog prior to addition to progHistory.
        Updates prog to the next available position after insertion.
        Assumes placement has already been validated.
        """
        if (dist < 0):
            raise Exception(f"Attempted to add unit at negative distance from prog")
        i = self.prog + dist
        if (i + self.hint.view() > len(self.cellList)):
            global iters
            print(self)
            raise Exception(f"Attempted to add unit of length {self.hint.view()} at index {i}, exceeding length {self.length}; iters={iters}")
        self.progHistory.append(self.prog)
        self.unitLocations.append(i)
        for j in range(i, i + self.hint.take()):
            self.cellList[j] += 1
        if (j + 1 != len(self.cellList)):
            self.cellList[j+1] -= 1
        self.prog = j + 2
        return self

    def __isub__(self, n):
        """
        Removes the last n units placed along this fiber.
        Restores prog to its prior value before these units were inserted.
        Pops these units' locations from unitLocations.
        """
        if (n > self.hint.prog):
            raise Exception(f"Attempted to remove {n} units with hint.prog {self.hint.prog}")
        for _ in range(n):
            i = self.unitLocations.pop()
            for j in range(i, i + self.hint.restore()):
                self.cellList[j] -= 1
            if (j + 1 != len(self.cellList)):
                self.cellList[j+1] += 1
            self.prog = self.progHistory.pop()
        return self

    def __len__(self):
        """
        Length is determined as total length - prog
        """
        return self.length - self.prog

    def __getitem__(self, i):
        return self.cellList[self.prog + i]

    def __setitem__(self, i, val):
        self.cellList[i] = val

    def __iter__(self):
        """
        Iteration begins at index prog
        """
        return iter(self.cellList[self.prog:])

    def incrementPermutation(self, perm, moveableSpace):
        for j in range(len(perm) - 1, -1, -1):
            perm[j] += 1
            if sum(perm) <= moveableSpace:
                break
            elif j == 0:
                break
            perm[j] = 0

    def validate(self, dist):
        """
        Validates placement of the current unit dist units from prog against the known empty cells in the fiber,
        returning False if there is a conflict, true otherwise.
        If placing the current unit at index i overwrites known data or attempts out of bound access, raises exception.
        If this fiber is complete, obviously any attempt at a placement is invalid.
        """
        if self.isComplete():
            return False
        i = self.prog + dist
        if (i < self.prog):
            raise Exception(f"Attempted to validate unit at index {i} with prog {self.prog}")
        if (i + self.hint.view() > len(self.cellList)):
            raise Exception(f"Attempted to validate unit of length {self.hint.view()} at index {i}, exceeding length {self.length}")
        for j in range(i, i + self.hint.view()):
            if (self.cellList[j] < 0):
                return False
            if (self.cellList[j] > 1):
                debug("Attempted to validate unit placement on full cell. This really shouldn't happen")
                return False
        if j + 1 < len(self.cellList):
            if self.cellList[j + 1] > 0:
                return False
        return True
    
    def isComplete(self):
        return self.hint.isComplete()

    def readPermutation(self, spaces):
        """
        Produces a generator object which yields a sequence of +1 and -1s corresponding to filled and empty cells.
        The sequence is of length len(fiber), after which a StopIteration is produced.
        This function does not verify that the permutation fits in the fiber.
        All spaces are padded by 1 on the right, so a space of 0 is actually a distance of 1 in the fiber.
        Usage: perm = readSuffixPermutation(...), while i < suffixLength: cell = next(perm)
        """
        hintIndex = 0
        i = 0
        while i < len(self):
            if hintIndex >= len(self.hint):
                yield -1
                i += 1
                continue
            for _ in range(spaces[hintIndex]):
                yield -1
                i += 1
            for _ in range(self.hint[hintIndex]):
                yield 1
                i += 1
            if (i < len(self)):
                yield -1
                i += 1
            hintIndex += 1

    def generateValidPermutations(self, skipFirstCell = False, mustIncludeFirstCell = False):
        """
        Produces a generator object which yields a sequence of valid permutations of the distances between remaining units.\n
        Units are assumed to be padded with one empty cell, so a distance of 0 in a permutation is actually a distance of 1 in the fiber.
        If self.isComplete, yields [] and stops iteration.
        """
        if (skipFirstCell and mustIncludeFirstCell):
            raise Exception("Contradiction in arguments to generateValidPermutations")
        
        if (self.isComplete()):
            yield []
            return
        cur = [0 for _ in self.hint]
        if skipFirstCell: cur[0] = 1
        filledCells = sum(self.hint)
        emptyCells = len(self) - filledCells
        moveableSpace = emptyCells - len(self.hint) + 1
        while cur[0] <= (0 if mustIncludeFirstCell else moveableSpace):
            perm = self.readPermutation(cur)
            #Check if the permutation is valid against the fiber
            for i in range(len(self)):
                cell = next(perm)
                if cell < 0 and self[i] > 0:
                    break
                elif cell > 0 and self[i] < 0:
                    break
            else:
                #The permutation is valid. Yield it
                yield cur
            #Increment the permutation
            self.incrementPermutation(cur, moveableSpace)

    def buildPermutationThenUndo(self, perm):
        """
        Precondition: Perm is guaranteed to be a valid permutation
        """
        for dist in perm:
            self += dist
        yield
        self -= len(perm)
        yield

    def trueIndexEnumerate(self, start):
        """
        Used for CrossSolver.buildInwardsThenUndo
        """
        for i in range(start, len(self.cellList)):
            yield (i, self.cellList[i])

    def trueIndexIterate(self, start):
        """
        Used for CrossSolver.buildInwardsThenUndo
        """
        for i in range(start, len(self.cellList)):
            yield self.cellList[i]

    def pushProg(self, i):
        """
        I think i should never be more than 1 greater than prog, so raise an exception if it occurs.
        Should never be called with i = 0.
        """
        if (i < 1):
            raise Exception("pushProg called with i < 1")
        if (self.prog + 1 < i):
            raise Exception(f"Cross index is far greater than prog: i = {i}, prog = {self.prog}")
        self.prog = max(self.prog, i)

    def pullProg(self, i):
        """
        Reverses pushProg(i).
        """
        if (i < 1):
            raise Exception("i < 1 on call to pullProg")
        if (self.prog < i):
            raise Exception(f"self.prog < i on call to pullProg")
        if (self.prog == i):
            if (self.cellList[i-1] < 1):
                self.prog -= 1
            elif (self.cellList[i-1] > 0):
                raise Exception(f"On call to pullProg, the cell right before prog is filled.")
            if (i - 2 >= 0):
                if (self.cellList[i-2] > 0):
                    self.prog += 1

    def __str__(self):
        global chars
        res = ""
        if (self.tag != ""):
            res += self.tag + ": "
        for i, cell in enumerate(self.cellList):
            #"On mac: ⯀□"
            #"✕"
            res += chars[cell.val + 2]
            res += " "
        res += "  prog = " + str(self.prog) + "\n"
        return res

    def __hash__(self):
        res = 0
        for i, cell in enumerate(self.cellList):
            res += hash(hash((i, cell.val)))
        return res%10000
 
class Cross:

    def __init__(self, i, row: Fiber, rowHint: list[int], col: Fiber, colHint: list[int]):
        """
        Crosses are formed by the composition of each row and column pair intersecting at the same index.
        Cross index is determined by diagonal distance from the top left corner of the grid.
        Row and col args are lists of GridCell objects, rowHint and colHint are lists of integer hints.
        """
        self.i = i
        self.rowLength = len(row)
        self.row = row
        self.colLength = len(col)
        self.col = col

    def isComplete(self):
        return self.row.isComplete() and self.col.isComplete()

    def generateValidPermutations(self):
        """
        Produces a generator object which yields a sequence of valid permutations of the distances between remaining units in this cross.\n
        Permutations are of the form (rowPerm, colPerm).
        """
        #If the row or the column progs are not yet at the intersection index, we have made a mistake somewhere
        if (self.row.prog < self.i or self.col.prog < self.i):
            raise Exception(f"Row and/or column progs don't exceed index {self.i}; row.prog: {self.row.prog}, col.prog: {self.col.prog}")
        
        #If the row or column progs are past the intersection index already, we don't need to consider the intersection
        if (self.row.prog > self.i or self.col.prog > self.i):
            #We can just permute the row and column as normal
            for rowPerm in self.row.generateValidPermutations():
                for colPerm in self.col.generateValidPermutations():
                    yield (rowPerm, colPerm)
        else:
            #We must individually consider the cases where the intersection cell is filled and not filled
            for rowPerm in self.row.generateValidPermutations(mustIncludeFirstCell=True):
                for colPerm in self.col.generateValidPermutations(mustIncludeFirstCell=True):
                    yield (rowPerm, colPerm)
            for rowPerm in self.row.generateValidPermutations(skipFirstCell=True):
                for colPerm in self.col.generateValidPermutations(skipFirstCell=True):
                    yield (rowPerm, colPerm)

    def buildPermutationThenUndo(self, perm: tuple[list[int], list[int]]):
        """
        Precondition: Perm is guaranteed to be a valid permutation
        """
        debug(f"Building permutation {perm}")
        for dist in perm[0]:
            pre = hash(self.row)
            self.row += dist
            self.row -= 1
            if (pre != hash(self.row)):
                raise Exception("FDSHJFDKDFJL")
            self.row += dist
        for dist in perm[1]:
            pre = hash(self.col)
            self.col += dist
            self.col -= 1
            if (pre != hash(self.col)):
                raise Exception("FDSHJFDKDFJL2")
            self.col += dist
        yield
        self.row -= len(perm[0])
        self.col -= len(perm[1])
        yield

    def pushProg(self, i):
        self.row.pushProg(i)
        self.col.pushProg(i)

    def pullProg(self, i):
        self.row.pullProg(i)
        self.col.pullProg(i)

class CrossSolver:

    def __init__(self, rowHints, colHints):
        self.rowHints = [Hint(hint) for hint in rowHints]
        self.colHints = [Hint(hint) for hint in colHints]
        self.numRows = len(rowHints)
        self.numCols = len(colHints)
        self.grid = [[GridCell() for c in range(self.numCols)] for r in range(self.numRows)]
        self.gridTranspose = [[self.grid[r][c] for r in range(self.numRows)] for c in range(self.numCols)]
        self.rows = [Fiber(self.grid[r], self.rowHints[r], f"Row {r}") for r in range(len(self.grid))]
        self.cols = [Fiber(self.gridTranspose[c], self.colHints[c], f"Col {c}") for c in range(len(self.gridTranspose))]
        self.crosses: list[Cross] = []
        self.printTime = -1
        for i in range(min(self.numRows, self.numCols)):
            self.crosses.append(Cross(i, self.rows[i], rowHints[i], self.cols[i], colHints[i]))

    def printGrid(self, stop = -1, chars = "✕✕□■■"):
        for i, r in enumerate(self.grid):
            for cell in r:
                #"On mac: ⯀□"
                #"✕"
                print(chars[cell + 2], end=" ")
            print()
            if (i == stop):
                break

    def __str__(self):
        global chars
        res = ""
        #if (not self.rowHints == None): res += str(self.rowHints) + "\n"
        #if (not self.colHints == None): res += str(self.colHints) + "\n"
        for i, r in enumerate(self.grid):
            for cell in r:
                #"On mac: ⯀□"
                #"✕"
                res += chars[cell + 2] + " "
            res += "\n"
        return res

    def buildInwardsThenUndo(self, i):
        pre = hash(self)
        failed = False
        edits = [[], []]
        j = i
        for rowCell, colCell in itertools.zip_longest(self.crosses[i].row.trueIndexIterate(i), self.crosses[i].col.trueIndexIterate(i)):
            if (rowCell == 1):
                if (not self.cols[j].validate(0)):
                    failed = True
                    break
                debug(self.cols[j].prog)
                self.cols[j] += 0
                debug(self)
                edits[0].append(j)
            if (colCell == 1):
                if (not self.rows[j].validate(0)):
                    failed = True
                    break
                self.rows[j] += 0
                edits[1].append(j)
            j += 1
        if not failed: 
            for row in self.rows:
                row.pushProg(i+1)
            for col in self.cols:
                col.pushProg(i+1)
        yield not failed
        if not failed:
            for row in self.rows:
                row.pullProg(i+1)
            for col in self.cols:
                col.pullProg(i+1)
        #Reverse downwards build
        for j in edits[0]:
            self.cols[j] -= 1
        #Reverse rightwards build
        for j in edits[1]:
            self.rows[j] -= 1
        if (pre != hash(self)):
            raise Exception("Undo operation failed somehow")
        yield

    def solve(self, i = 0, stop = -1):
        global iters, permProg, numPerms
        if i == 0:
            perms = self.crosses[i].generateValidPermutations()
            numPerms = 0
            while True:
                try:
                    next(perms)
                except StopIteration:
                    break
                numPerms += 1
            self.printTime = time.perf_counter()
        if i >= len(self.crosses): return True
        perms = self.crosses[i].generateValidPermutations()
        while True:
            if permProg % 100000 == 0:
                print(f"Estimated progress: {permProg} / {numPerms} = {round(permProg/numPerms, 2)}")
                print(self)
                print("\n\n")
            """
            if time.perf_counter() > self.printTime:
                print(f"Estimated progress: {permProg} / {numPerms} = {round(permProg/numPerms, 2)}")
                print(self)
                print("\n\n")
                self.printTime += 3
            """
            if (iters == stop): break
            try:
                cand = next(perms)
                permProg += 1
            except StopIteration:
                debug(f"No more permutations available for {i}")
                break
            pre = hash(self)
            step1 = self.crosses[i].buildPermutationThenUndo(cand)
            step2 = self.buildInwardsThenUndo(i)
            next(step1)
            debug(f"Cross {i}: {cand}")
            debug(self)
            debug("Building inwards:")
            if next(step2): #Building inwards may reject some permutations
                debug(self)
                debug(f"permutation of cross {i} accepted, moving to cross {i+1}")
                if self.solve(i + 1): return True
                debug(f"permutation of cross {i+1} failed, returning to cross {i}")
            else:
                debug("Inwards build regected cand.")
            next(step2)
            next(step1)
            if (pre != hash(self)):
                raise Exception("Grid modification not undone properly")
            iters += 1
        return False

    def __hash__(self):
        res = 0
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                res += hash((r, c, cell.val))
        return res%10000


if __name__ == "__main__":
    site = "nonograms.org"

    rowHints = []
    colHints = []
    if (rowHints == []):
        url: str = input(f"Enter the URL to the puzzle from nonograms.org or puzzle-nonograms.com: ")
        site = None
        if "nonograms.org" in url:
            site = "nonograms.org"
        if "puzzle-nonograms.com" in url:
            site = "puzzle-nonograms.com"
        match site:
            case "nonograms.org":
                rowHints, colHints = puzzle_nonograms_getHints(url)
            case "puzzle-nonograms.com":
                rowHints, colHints = nonograms_org_getHints(url)
            case _:
                raise Exception(f"Invalid url {url}")

    print(rowHints)
    print(colHints)

    start = time.perf_counter()
    solver = CrossSolver(rowHints, colHints)
    solver.solve()
    end = time.perf_counter()
    dur = end - start
    print(f"Solution took {dur:.6f} seconds.")
    #Benchmark time: ___
    print(solver)