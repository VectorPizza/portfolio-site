#!/usr/bin/env python3
"""Build the live homepage (index.html) from the Chassis design.

usage: python3 chassis_build.py <chassis_dir> <site_dir>
Run after export.py: replaces site/index.html; project pages stay as exported.
- copies the Chassis media it uses into site/assets/c/
- makes project links relative and same-tab
- applies live-site choices: Vector Pizza logo thumbnail, Homecoming hover rests at 1s,
  sharper Paragon loop on the Paragon card
- adds head meta, favicon, GoatCounter and the hidden visit counter
"""
import html, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.dirname(HERE)
SRC, OUT = sys.argv[1], sys.argv[2]
DOMAIN = 'austinremer.com'
TITLE = 'Austin Remer — Designer'
DESC = 'Austin Remer designs brands, from the logo to everything it ends up on: screens, print, merch and spaces.'

s = open(os.path.join(SRC, 'index.html')).read()
# preview-only tuning panel never goes live
s = re.sub(r'\n?<!--TUNE-->.*?<!--/TUNE-->\n?', '\n', s, flags=re.S)

def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (a[:70], c)
    s = s.replace(a, b)

# --- media that lives outside the Chassis folder
extra = {
    'homecoming.mp4': os.path.join(SCRATCH, 'portfolio/img/hog/logo-loop.mp4'),
    'vp-logo.png': os.path.join(SCRATCH, 'portfolio/img/vp/vp-logo.png'),
    'homecoming-1s.jpg': os.path.join(SCRATCH, 'portfolio/img/hog/homecoming-1s.jpg'),
}

# Paragon card: same sharper loop as the header
rep('src="assets/paragon.mp4" poster="assets/paragon.jpg"', 'src="assets/paragon-blast.mp4" poster="assets/paragon-blast.jpg"')

# Homecoming card: rest on the 1s frame, restart from 0 on hover
rep('<video class="hover" src="assets/homecoming.mp4" poster="assets/hog-homecoming.jpg" muted loop playsinline preload="none"',
    '<video class="hover" data-rest="1" src="assets/homecoming.mp4" poster="assets/homecoming-1s.jpg" muted loop playsinline preload="metadata"')
rep("card.addEventListener('mouseleave', function(){ v.pause(); try{ v.currentTime=0; }catch(e){} });",
    "card.addEventListener('mouseleave', function(){ v.pause(); try{ v.currentTime=+(v.dataset.rest||0); }catch(e){} });\n"
    "    if(v.dataset.rest){ var r=+v.dataset.rest; var go=function(){ try{ v.currentTime=r; }catch(e){} }; if(v.readyState>=1) go(); else v.addEventListener('loadedmetadata',go,{once:true}); }")
rep("card.addEventListener('mouseenter', function(){ v.preload='auto'; var p=v.play();",
    "card.addEventListener('mouseenter', function(){ v.preload='auto'; try{ v.currentTime=0; }catch(e){} var p=v.play();")

# Vector Pizza card: the logo, as on the old homepage
rep('<div class="frame"><img src="assets/vp-patches.jpg" alt="Vector Pizza space patches laid out on black: Apollo, Discovery and Mercury designs" loading="lazy"></div>',
    '<div class="frame light vp"><img src="assets/vp-logo.png" alt="Vector Pizza logo: a pizza slice in a scalloped orange seal" loading="lazy"></div>')
rep('.frame.light{background:#efefef}',
    '.frame.light{background:#efefef}\n.frame.vp{display:flex;align-items:center;justify-content:center;background:#e4e2dc}\n'
    '.frame.vp img{position:static;inset:auto;width:156%;max-width:none;height:auto;object-fit:contain}')

# links: relative, same tab (résumé still opens in a new tab)
s = re.sub(r'href="https://austinremer\.com/([^"]+\.html)" target="_blank" rel="noopener"', r'href="\1"', s)
s = s.replace('href="https://austinremer.com/Austin_Remer_Resume.pdf"', 'href="Austin_Remer_Resume.pdf"')
assert 'https://austinremer.com/' not in s.replace('https://austinremer.com/hall-of-game-paragon.html', ''), 'absolute link left'
s = s.replace('href="https://austinremer.com/hall-of-game-paragon.html" target="_blank" rel="noopener"', 'href="hall-of-game-paragon.html"')

# hidden visit counter, same color as the footer background
rep('<span class="mono dim">© 2026 Austin Remer</span>',
    '<span class="mono dim">© 2026 Austin Remer<span id="visits" aria-hidden="true" style="margin-left:14px;color:#1a1917;user-select:text">Visits: …</span></span>'
    '<script>fetch("https://arportfolio.goatcounter.com/counter/TOTAL.json").then(function(r){return r.json()})'
    '.then(function(d){document.getElementById("visits").textContent="Visits: "+d.count}).catch(function(){})</script>')

# --- split head/body and wrap
k = s.index('<header class="top">')
head, body = s[:k], s[k:]
head = re.sub(r'<title>[^<]*</title>\s*', '', head)
page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(TITLE)}</title>
<meta name="description" content="{html.escape(DESC, quote=True)}">
<meta property="og:title" content="{html.escape(TITLE, quote=True)}">
<meta property="og:description" content="{html.escape(DESC, quote=True)}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://{DOMAIN}/">
<meta property="og:image" content="https://{DOMAIN}/assets/868f838a37c571f33ea0e57ef53c3486.jpg">
<meta name="theme-color" content="#1a1917">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%232a2a2a'/%3E%3Ctext x='16' y='22' font-family='Helvetica,Arial,sans-serif' font-size='16' fill='%23efeee9' text-anchor='middle'%3EAR%3C/text%3E%3C/svg%3E">
<style>html{{background:#1a1917}}body{{margin:0}}img{{max-width:100%}}</style>
{head.strip()}
<script data-goatcounter="https://arportfolio.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head>
<body>
{body.strip()}
</body>
</html>
'''

# --- media: copy what the page uses into assets/c/
os.makedirs(os.path.join(OUT, 'assets', 'c'), exist_ok=True)
used = sorted(set(re.findall(r'"assets/([^"/]+)"', page)))
for name in used:
    src = os.path.join(SRC, 'assets', name)
    if name in extra:
        src = extra[name]
    assert os.path.exists(src), ('missing media', name)
    shutil.copyfile(src, os.path.join(OUT, 'assets', 'c', name))
page = re.sub(r'"assets/([^"/]+)"', r'"assets/c/\1"', page)
open(os.path.join(OUT, 'index.html'), 'w').write(page)
print(f'chassis homepage: {len(used)} media files')
