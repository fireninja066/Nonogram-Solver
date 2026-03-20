from playwright.sync_api import sync_playwright

def puzzle_nonograms_getHints(url):
    rowHints = []
    colHints = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("td.nmtl")
        nmtl = page.query_selector("td.nmtl")
        rows = nmtl.query_selector_all("tr")
        for tr in rows:
            nums = [
                int(td.text_content().strip())
                for td in tr.query_selector_all("td.num")
            ]
            rowHints.append(nums)
        page.wait_for_selector("td.nmtt")
        nmtt = page.query_selector("td.nmtt")
        rows = nmtt.query_selector_all("tr")
        numCols = max(len(tr.query_selector_all("td")) for tr in rows)
        colHints = [[] for _ in range(numCols)]
        for tr in rows:
            cells = tr.query_selector_all("td")
            for c, td in enumerate(cells):
                try:
                    val = int(td.text_content().strip())
                    colHints[c].append(val)
                except: pass
        """
        for i, row in enumerate(rowHints): print(f"row {i}:", row)
        for i, col in enumerate(colHints): print(f"col {i}:", col)
        """
        browser.close()
    return rowHints, colHints

def nonograms_org_getHints(url):
    rowHints = []
    colHints = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("div.task-cell.selectable")
        rows = page.query_selector_all("#taskLeft .task-group")
        cols = page.query_selector_all("#taskTop .task-group")
        for i, row in enumerate(rows):
            cells = row.query_selector_all(".task-cell")
            rowData = [
                int(c.text_content().strip())
                for c in cells if c.text_content() != ''
            ]
            #print(f"row {i}:", rowData)
            rowHints.append(rowData)
        colHints = []
        for i, col in enumerate(cols):
            cells = col.query_selector_all(".task-cell")
            colData = [
                int(c.text_content().strip())
                for c in cells if c.text_content() != ''
            ]
            #print(f"col {i}:", colData)
            colHints.append(colData)
        browser.close()
    return rowHints, colHints