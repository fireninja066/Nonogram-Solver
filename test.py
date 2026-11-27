from playwright.sync_api import sync_playwright

JS = """
() => {
    const out = [];
    document.querySelectorAll('body *').forEach(el => {
        const own = Array.from(el.childNodes)
            .filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('');
        if (/^\\d+$/.test(own)) {
            const chain = [];
            for (let n = el, i = 0; n && i < 4; n = n.parentElement, i++)
                chain.push(n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') +
                           (n.className ? '.' + String(n.className).split(' ').join('.') : ''));
            out.push({
                text: own,
                chain: chain.join(' < '),
                bg: getComputedStyle(el).backgroundColor,
                color: getComputedStyle(el).color,
                html: el.outerHTML.slice(0, 200)
            });
        }
    });
    return out;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.nonograms.org/nonograms2/i/84239")
    page.wait_for_timeout(5000)  # just let the page finish rendering
    hits = page.evaluate(JS)
    print(len(hits), "numeric elements")
    for h in hits[:12]:
        print(h)
    browser.close()