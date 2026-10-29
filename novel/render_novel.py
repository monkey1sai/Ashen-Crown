"""Render the manuscript into a self-contained, offline HTML reader."""
from pathlib import Path
import hashlib
import html
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = HERE / "灰燼之冠.md"
text = SOURCE.read_text(encoding="utf-8")
chunks = re.split(r"^## (.+)$", text, flags=re.M)
assert chunks[0].strip() == "# 灰燼之冠", "Unexpected manuscript opening"
assert len(chunks) == 41, "Expected 20 chapters"
for term in ("UI", "QTE", "玩家", "本篇預設", "抉擇結果", "狀態變化", "自我值"):
    assert term not in text, f"Production marker in manuscript: {term}"

toc, chapters = [], []
for i in range(1, len(chunks), 2):
    number = (i + 1) // 2
    heading, body = chunks[i].strip(), chunks[i + 1].strip()
    assert body, f"Empty chapter {number}"
    anchor = f"chapter-{number}"
    toc.append(f'<li><a href="#{anchor}">{html.escape(heading)}</a></li>')
    paragraphs = "\n".join(f"<p>{html.escape(p.strip())}</p>" for p in body.split("\n\n") if p.strip())
    chapters.append(f'<section id="{anchor}"><h2>{html.escape(heading)}</h2>\n{paragraphs}</section>')

page = '''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>灰燼之冠｜小說閱讀版</title>
<style>
:root{color-scheme:light dark;--paper:#f5f0e7;--ink:#302c28;--muted:#756b5e;--line:#d9cebb;--accent:#7b512b}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:2rem}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif TC","Source Han Serif TC","Microsoft JhengHei",serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}a:focus-visible{outline:2px solid var(--accent);outline-offset:4px}
.layout{max-width:1240px;margin:auto;display:grid;grid-template-columns:255px minmax(0,1fr);gap:60px;padding:56px 32px}
aside{position:sticky;top:24px;align-self:start;max-height:calc(100vh - 48px);overflow:auto;font-family:"Microsoft JhengHei",sans-serif;font-size:14px;line-height:1.7}
aside h2{font-size:14px;color:var(--muted);letter-spacing:.18em}ol{list-style:none;padding:0}li{margin:0 0 12px}
main{min-width:0;max-width:740px}header{padding:36px 0 64px;border-bottom:1px solid var(--line)}
.eyebrow{font-family:serif;font-size:14px;letter-spacing:.2em;color:var(--muted)}h1{font-size:52px;font-weight:500;letter-spacing:.16em;margin:22px 0}header p{color:var(--muted);font-size:15px;line-height:1.8}
section{padding:64px 0 48px;border-bottom:1px solid var(--line)}section h2{font-size:27px;font-weight:500;line-height:1.6;margin:0 0 38px}
section p{font-size:19px;line-height:2.1;letter-spacing:.035em;margin:0 0 1.25em;overflow-wrap:break-word}
footer{padding:40px 0 80px;color:var(--muted);font-size:14px;line-height:1.9}.top{position:fixed;right:18px;bottom:18px;background:var(--paper);border:1px solid var(--line);padding:9px 13px;font-size:13px}
@media(max-width:900px){.layout{display:block;max-width:760px;padding:24px}aside{position:static;max-height:none;border-bottom:1px solid var(--line);padding-bottom:20px}aside ol{columns:2;column-gap:24px}li{break-inside:avoid}header{padding:40px 0}h1{font-size:42px}section{padding-top:46px}}
@media(max-width:480px){.layout{padding:22px}aside ol{columns:1}aside details:not([open]) ol{display:none}h1{font-size:36px}section h2{font-size:25px}section p{font-size:18px;line-height:2}}
@media(prefers-color-scheme:dark){:root{--paper:#201f1c;--ink:#e5ddce;--muted:#afa28f;--line:#464035;--accent:#d5b582}}
@media print{aside,.top{display:none}.layout{display:block;padding:0}body{background:white;color:black}main{max-width:none}header{break-after:page}section{break-before:page;border:0;padding:0}section p{font-size:11pt;line-height:1.8}h2{break-after:avoid}p{orphans:3;widows:3}footer{padding:20px 0}}
</style></head><body id="top"><div class="layout">
<aside aria-label="章節目錄"><details open><summary>章節目錄</summary><ol>__TOC__</ol></details></aside>
<main><header><div class="eyebrow">ASHEN CROWN</div><h1>灰燼之冠</h1><p>小說閱讀版 · 二十章</p><p>依 day-000 至 day-042 預設故事線整理。<br>故事截至第二十二天早晨，未完待續。</p></header>
__CHAPTERS__
<footer>本閱讀版截至 2026 年 10 月 29 日的連載進度。<br>尚未揭曉的故事，留待後續篇章。<br><a href="灰燼之冠.md">Markdown 正文</a> · <a href="來源與校對.md">來源與校對</a></footer>
</main></div><a class="top" href="#top" aria-label="回到目錄">回目錄 ↑</a></body></html>'''
page = page.replace("__TOC__", "\n".join(toc)).replace("__CHAPTERS__", "\n".join(chapters))
(HERE / "灰燼之冠.html").write_text(page, encoding="utf-8")

ranges = [(0,2),(3,4),(5,6),(7,9),(10,11),(12,12),(13,14),(15,16),(17,18),(19,19),(20,21),(22,24),(25,26),(27,28),(29,30),(31,33),(34,35),(36,37),(38,40),(41,42)]
covered = [n for start,end in ranges for n in range(start,end+1)]
assert covered == list(range(43)), "Source coverage mismatch"
daily = [ROOT / "daily" / f"day-{n:03d}.md" for n in covered]
manifest = {
    "base_commit": "d4a1ad4d93019f1193258026149f08e1309fbeb2",
    "latest_episode": "day-042",
    "route": "default",
    "chapter_sources": {str(i): [f"day-{n:03d}" for n in range(a,b+1)] for i,(a,b) in enumerate(ranges,1)},
    "sources": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in daily + [ROOT / "bible.md", ROOT / "summary.md", ROOT / "program.md"]},
    "manuscript_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "html_sha256": hashlib.sha256((HERE / "灰燼之冠.html").read_bytes()).hexdigest(),
}
(HERE / "source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"chapters":len(chapters),"episodes":len(daily),"han_characters":len(re.findall(r"[\u4e00-\u9fff]",text)),"output":"灰燼之冠.html","coverage":"PASS","production_markers":"PASS"},ensure_ascii=False))
