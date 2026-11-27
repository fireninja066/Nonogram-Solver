from playwright.sync_api import sync_playwright
import re

def puzzle_nonograms_getHints(url):
    rowHints = []
    colHints = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
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
        cols = nmtt.query_selector_all("tr")
        numCols = max(len(tr.query_selector_all("td")) for tr in cols)
        colHints = [[] for _ in range(numCols)]
        for tr in cols:
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
        browser = p.chromium.launch(headless=False)
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

def _css_to_hex(css, default="#000000"):
    """Convert 'rgb(r, g, b)' / 'rgba(r, g, b, a)' to '#rrggbb'.
    Transparent or unparseable values fall back to black."""
    try:
        nums = [float(n) for n in css[css.index("(") + 1 : css.index(")")].split(",")]
        if len(nums) == 4 and nums[3] == 0:
            return default
        r, g, b = (int(n) for n in nums[:3])
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return default

def nonograms_org_getHints(url):
    rowHints = []
    colHints = []
    rowHintColors = []
    colHintColors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("td.num, div.task-cell.selectable")

        if page.query_selector("td.num") is None:
            # ---- original algorithm (pages using div.task-cell), default black ----
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
                rowHintColors.append(["#000000"] * len(rowData))
            colHints = []
            for i, col in enumerate(cols):
                cells = col.query_selector_all(".task-cell")
                colData = [
                    int(c.text_content().strip())
                    for c in cells if c.text_content() != ''
                ]
                #print(f"col {i}:", colData)
                colHints.append(colData)
                colHintColors.append(["#000000"] * len(colData))
        else:
            # ---- colour pages: hint cells are td.num with ids like nmv9_0 ----
            groups = {}  # kind -> {line index -> [(pos, number, color, element)]}
            for c in page.query_selector_all("td.num"):
                m = re.fullmatch(r"nm([a-z]+)(\d+)_(\d+)", c.get_attribute("id") or "")
                text = c.text_content().strip()
                if not m or not text.isdigit():
                    continue
                kind, line, pos = m.group(1), int(m.group(2)), int(m.group(3))
                color = _css_to_hex(c.evaluate("e => getComputedStyle(e).backgroundColor"))
                groups.setdefault(kind, {}).setdefault(line, []).append(
                    (pos, int(text), color, c)
                )

            for kind, kg in groups.items():
                # Decide orientation: do this kind's hints stack vertically (columns)?
                biggest = sorted(max(kg.values(), key=len), key=lambda t: t[0])
                b0 = biggest[0][3].bounding_box()
                b1 = biggest[-1][3].bounding_box()
                if len(biggest) > 1 and b0 and b1:
                    isCol = abs(b1["y"] - b0["y"]) > abs(b1["x"] - b0["x"])
                else:
                    isCol = (kind == "v")  # fallback guess

                for line in sorted(kg):
                    cells = sorted(kg[line], key=lambda t: t[0])
                    data = [t[1] for t in cells]
                    colors = [t[2] for t in cells]
                    if isCol:
                        colHints.append(data)
                        colHintColors.append(colors)
                    else:
                        rowHints.append(data)
                        rowHintColors.append(colors)
        browser.close()
    return rowHints, colHints, rowHintColors, colHintColors

if __name__ == "__main__":
    r, c, rc, cc = nonograms_org_getHints("https://www.nonograms.org/nonograms2/i/84239")
    print(len(r), len(c))        # expect 19 21
    print(r[0], rc[0])           # expect [3, 3] and two colors
    print(c[9], cc[9])           # expect the 10-entry column