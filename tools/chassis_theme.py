#!/usr/bin/env python3
"""Convert the light project pages (.dc.html) to the Chassis theme, in place.

usage: python3 chassis_theme.py <page.dc.html> [...]
- swaps the light palette for the Chassis tokens in inline styles
  (elements sitting on their own light background, like color swatches, are left alone)
- dark helmet CSS, Geist Mono, mono uppercase labels, orange section numbers
- replaces the header with the Chassis top bar
Idempotent: pages already converted are skipped.
"""
import re, sys

CH = {'chassis': '#1a1917', 'panel': '#22211e', 'rule': '#3a3832', 'alu': '#d4d2cc',
      'dim': '#8f8c84', 'paper': '#eeede9', 'signal': '#f06a26'}

COLOR = {'#2a2a2a': CH['alu'], '#4f4d48': '#b3b0a8', '#67655f': CH['dim'], '#85827a': CH['dim'], '#efeee9': CH['paper']}
BG = {'#efeee9': CH['chassis'], '#21201e': CH['panel']}
BORDER = {'#2a2a2a': CH['alu'], '#c8c5bd': CH['rule']}

def lum(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def restyle(style):
    bgs = re.findall(r'background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})\b', style)
    if any(b.lower() != '#efeee9' and lum(b) > 0.7 for b in bgs):
        return style  # its own light surface (swatch, light image tile): keep as designed
    style = re.sub(r'(background(?:-color)?:\s*)(#[0-9a-fA-F]{3,6})\b',
                   lambda m: m.group(1) + BG.get(m.group(2).lower(), m.group(2)), style)
    style = re.sub(r'((?<![-\w])color:\s*)(#[0-9a-fA-F]{3,6})\b',
                   lambda m: m.group(1) + COLOR.get(m.group(2).lower(), m.group(2)), style)
    style = re.sub(r'(border(?:-top|-bottom|-left|-right)?:\s*1px solid\s*)(#[0-9a-fA-F]{3,6})\b',
                   lambda m: m.group(1) + BORDER.get(m.group(2).lower(), m.group(2)), style)
    return style

THEME_CSS = '''
/* chassis theme */
html{background:#1a1917;color-scheme:dark}
::selection{background:#f06a26;color:#1a1917}
#top h1,#top h2,#top h3,#top .next-title{color:#eeede9}
#top h2>span:first-child{font-family:"Geist Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;letter-spacing:.06em;color:#f06a26!important}
#top dt{font-family:"Geist Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12.5px!important;letter-spacing:.06em;text-transform:uppercase}
#top footer{font-family:"Geist Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12.5px!important;letter-spacing:.06em;text-transform:uppercase}
#top footer a:hover{color:#eeede9!important}
.chtop{position:sticky;top:0;z-index:20;background:color-mix(in oklab,#1a1917 92%,transparent);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);border-bottom:1px solid #3a3832}
.chtop-in{max-width:1440px;margin:0 auto;padding:0 clamp(16px,2.4vw,36px);box-sizing:border-box;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:4px 28px;min-height:56px;font-size:17px;line-height:1.4;letter-spacing:-.01em;color:#d4d2cc}
.chtop a{text-decoration:none;color:#d4d2cc}
.chtop a:hover{color:#eeede9}
.chtop nav{display:flex;flex-wrap:wrap;gap:0 22px}
.chtop nav a,.chtop .name{padding:12px 0}
.chtop .role{color:#8f8c84}
.chtop .status{display:flex;align-items:center;gap:9px;font-family:"Geist Mono",ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;letter-spacing:.06em;text-transform:uppercase}
.chtop .led{width:8px;height:8px;border-radius:50%;background:#f06a26;box-shadow:0 0 0 3px color-mix(in oklab,#f06a26 22%,transparent)}
@media (max-width:640px){.chtop .role{display:none}}
'''

TOPBAR = '''<header class="chtop">
<div class="chtop-in">
<a class="name" href="Main.dc.html">Austin Remer</a>
<span class="role">Designer, Orlando FL</span>
<nav aria-label="Main"><a href="Main.dc.html#work">Work</a><a href="Main.dc.html#archive">Archive</a><a href="Main.dc.html#about">About</a><a href="Main.dc.html#contact">Contact</a></nav>
<span class="status"><span class="led" aria-hidden="true"></span>Open to art director roles</span>
</div>
</header>'''

for path in sys.argv[1:]:
    s = open(path).read()
    if '/* chassis theme */' in s:
        print('skip (already chassis)', path); continue
    # helmet
    s = s.replace('family=Geist:wght@400;500&amp;', 'family=Geist:wght@400;500&amp;family=Geist+Mono:wght@400;500&amp;', 1)
    s = s.replace('body{margin:0;background:#efeee9}', 'body{margin:0;background:#1a1917}', 1)
    s = s.replace('a{color:#2a2a2a}a:hover{color:#000000}', 'a{color:#d4d2cc}a:hover{color:#eeede9}', 1)
    s = s.replace('</style>\n</helmet>', THEME_CSS + '</style>\n</helmet>', 1)
    assert '/* chassis theme */' in s, ('no helmet style', path)
    # header
    s, n = re.subn(r'<header style="[^"]*">[\s\S]*?</header>', TOPBAR, s, count=1)
    assert n == 1, ('header not found', path)
    # inline styles in the body only (not the helmet, not the script)
    k = s.index('</helmet>')
    head, body = s[:k], s[k:]
    body = re.sub(r'style="([^"]*)"', lambda m: 'style="' + restyle(m.group(1)) + '"', body)
    s = head + body
    open(path, 'w').write(s)
    print('chassis', path)
