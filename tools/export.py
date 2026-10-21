#!/usr/bin/env python3
"""Export the Claude Design portfolio artifact (.dc.html pages) to a static site.

usage: python3 export.py <project_dir> <out_dir>
- renders {{holes}}, <sc-for>, <sc-if> using each page's renderVals() (via vals.js)
- rewrites /_blob/<id> to assets/<id>.<ext> (files located via found.json hash map)
- rewrites X.dc.html links to clean file names
- turns cards that link nowhere (href="#work") into non-clickable blocks
"""
import html, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.dirname(HERE)
SRC, OUT = sys.argv[1], sys.argv[2]

PAGES = {
    'Main.dc.html': ('index.html', 'Austin Remer — Designer',
                     'Austin Remer designs brands, from the logo to everything it ends up on: screens, print, merch and spaces.'),
    'HallOfGame.dc.html': ('hall-of-game-homecoming.html', 'Hall of Game: Homecoming 2025 — Austin Remer',
                           'Brand, event assets and broadcast graphics for Full Sail University’s esports homecoming.'),
    'ArmadaHQ.dc.html': ('armada-hq.html', 'Armada HQ — Austin Remer',
                         'Environmental design for Full Sail’s first ground-up esports center.'),
    'InfiniteArenas.dc.html': ('hall-of-game-infinite-arenas.html', 'Hall of Game: Infinite Arenas — Austin Remer',
                               'The 2022 edition of Hall of Game, with a 3D logo and arena screens.'),
    'NASA.dc.html': ('nasa-schematic-illustrations.html', 'NASA Schematic Illustrations — Austin Remer',
                     'Cutaway illustrations of NASA’s crewed spacecraft.'),
    'Infographics.dc.html': ('game-infographics.html', 'Game Infographics — Austin Remer',
                             'A social series of game infographics for Full Sail Armada.'),
    'Logos.dc.html': ('logos-and-marks.html', 'Logos and Marks — Austin Remer',
                      'Logos for events, programs and places.'),
    'VectorPizza.dc.html': ('vector-pizza.html', 'Vector Pizza — Austin Remer',
                            'Stickers, pins, patches and packaging for my own Etsy shop.'),
    'Paragon.dc.html': ('hall-of-game-paragon.html', 'Hall of Game: Paragon — Austin Remer',
                        'The 2023 Hall of Game, built around supernatural key art.'),
    'ArmadaBrand.dc.html': ('full-sail-armada.html', 'Full Sail Armada — Austin Remer',
                            'The Full Sail Armada esports brand, created in 2018 and redesigned each season.'),
    'Stellar.dc.html': ('stellar.html', 'Stellar — Austin Remer',
                        'An unproduced branding direction for Full Sail University’s 11th Hall of Fame.'),
    'Murals.dc.html': ('murals.html', 'Murals — Austin Remer',
                       'Two paint-by-number murals for Full Sail University’s Hall of Fame Week.'),
    'Purdue.dc.html': ('purdue-space-patch.html', 'Purdue Space Patch — Austin Remer',
                       'Mission patches for Purdue University’s Mars Perseverance merchandise.'),
    'Keyboard.dc.html': ('mysterium-keyboard.html', 'Mysterium Keyboard — Austin Remer',
                         'A keyboard I built from PCB design files and a parts list: KiCad, ordering boards, sourcing parts and a lot of soldering.'),
}
EXTRA_FILES = {'Austin_Remer_Resume.pdf': os.path.join(SCRATCH, 'portfolio', 'Austin_Remer_Resume.pdf')}
DOMAIN = 'austinremer.com'

found = json.load(open(os.path.join(SCRATCH, 'found.json')))
amap = {l.split()[0]: l.split()[1] for l in open(os.path.join(SCRATCH, 'assetmap.txt')) if l.strip()}


def lookup(path, scope):
    cur = scope
    for part in path.strip().split('.'):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(path)
    return cur


def holes(text, scope):
    def sub(m):
        expr = m.group(1).strip()
        if expr in ('false', 'true'):
            return expr
        v = lookup(expr, scope)
        if isinstance(v, bool):
            return 'true' if v else 'false'
        return html.escape(str(v), quote=True)
    return re.sub(r'\{\{([^}]*)\}\}', sub, text)


def render(body, vals):
    def do_if(text, scope):
        pat = re.compile(r'<sc-if value="\{\{([^}]*)\}\}"[^>]*>([\s\S]*?)</sc-if>')
        return pat.sub(lambda m: m.group(2) if lookup(m.group(1), scope) else '', text)

    def do_for(m):
        lst = lookup(m.group(1), vals)
        name, inner = m.group(2), m.group(3)
        out = []
        for item in lst:
            scope = dict(vals); scope[name] = item
            out.append(holes(do_if(inner, scope), scope))
        return ''.join(out)
    body = re.sub(r'<sc-for list="\{\{([^}]*)\}\}" as="([a-z]+)"[^>]*>([\s\S]*?)</sc-for>', do_for, body)
    body = do_if(body, vals)
    return holes(body, vals)


def static_cards(body):
    """Cards with href="#work" have no page yet: render as plain blocks, not links."""
    out, i = [], 0
    pat = '<a href="#work" class="card"'
    while True:
        j = body.find(pat, i)
        if j < 0:
            out.append(body[i:]); break
        k = body.index('</a>', j)
        out.append(body[i:j])
        out.append('<div class="card card-static"' + body[j + len(pat):k] + '</div>')
        i = k + len('</a>')
    return ''.join(out)


os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
used = set()
for src, (dst, title, desc) in PAGES.items():
    s = open(os.path.join(SRC, src)).read()
    vals = json.loads(subprocess.check_output(['node', os.path.join(HERE, 'vals.js'), os.path.join(SRC, src)]))
    helmet = re.search(r'<helmet>([\s\S]*?)</helmet>', s).group(1)
    body = re.search(r'</helmet>([\s\S]*?)</x-dc>', s).group(1)
    body = static_cards(render(body, vals))
    helmet = render(helmet, vals)
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://{DOMAIN}/{'' if dst == 'index.html' else dst}">
<meta property="og:image" content="https://{DOMAIN}/assets/868f838a37c571f33ea0e57ef53c3486.jpg">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%232a2a2a'/%3E%3Ctext x='16' y='22' font-family='Helvetica,Arial,sans-serif' font-size='16' fill='%23efeee9' text-anchor='middle'%3EAR%3C/text%3E%3C/svg%3E">
{helmet.strip()}
<style>.card-static{{cursor:default}}.card-static:hover .card-title{{text-decoration:none!important}}.card-static:hover .card-img{{transform:none!important;filter:none!important}}</style>
</head>
<body>
{body.strip()}
</body>
</html>
'''
    # links between pages
    for s2, (d2, _, _) in PAGES.items():
        page = page.replace(f'href="{s2}', f'href="{d2}')
    page = page.replace('href="index.html"', 'href="./"').replace('href="index.html#', 'href="./#')
    # analytics (live site only)
    page = page.replace('</head>', '<script data-goatcounter="https://arportfolio.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>\n</head>', 1)
    if dst == 'index.html':
        hidden = ('<span id="visits" aria-hidden="true" style="padding: 13px 0; color: #efeee9; user-select: text">Visits: …</span>'
                  '<script>fetch("https://arportfolio.goatcounter.com/counter/TOTAL.json").then(function(r){return r.json()})'
                  '.then(function(d){document.getElementById("visits").textContent="Visits: "+d.count}).catch(function(){})</script>')
        k = page.rfind('<span style="padding: 13px 0">© 2026 Austin Remer</span>')
        assert k > 0
        e = k + len('<span style="padding: 13px 0">© 2026 Austin Remer</span>')
        page = page[:e] + hidden + page[e:]
    # assets
    def asset(m):
        i = m.group(1); used.add(i)
        return f'assets/{i}.{amap[i]}'
    page = re.sub(r'/_blob/([0-9a-f]{32})', asset, page)
    left = re.findall(r'\{\{|<sc-|\.dc\.html|_blob', page)
    assert not left, (src, left[:5])
    open(os.path.join(OUT, dst), 'w').write(page)

for i in used:
    shutil.copyfile(os.path.join(SCRATCH, found[i]), os.path.join(OUT, 'assets', f'{i}.{amap[i]}'))
for name, path in EXTRA_FILES.items():
    shutil.copyfile(path, os.path.join(OUT, name))
open(os.path.join(OUT, 'CNAME'), 'w').write(DOMAIN + '\n')
open(os.path.join(OUT, '.nojekyll'), 'w').write('')
print(f'pages {len(PAGES)}, assets {len(used)}')
