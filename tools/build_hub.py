# schools.json + src/hub.html → site/index.html  (카드를 HTML 에 직접 써서 검색엔진도 보게)
# usage: python3 tools/build_hub.py
import html, json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
URL, REPO = "https://seojooyeon-creat.github.io/smashhigh/", "https://github.com/Seojooyeon-creat/smashhigh"
tpl = (root / "src" / "hub.html").read_text(encoding="utf-8")
schools = sorted(json.loads((root / "schools.json").read_text(encoding="utf-8")), key=lambda s: s["name"])
e = lambda v: html.escape(str(v), quote=True)
cards = "".join(
    f'<a class="card" href="{e(s["code"])}/" data-key="{e((s["name"] + " " + s.get("short", "") + " " + s.get("region", "")).lower())}">'
    f'<img src="{e(s["code"])}/og.png" alt="{e(s["name"])}가 부서지는 게임 화면" loading="lazy" width="1200" height="630">'
    f'<div class="body"><span class="code">SMASH {e(s.get("short", s["name"]))}</span><span class="name">{e(s["name"])}</span>'
    f'<span class="region">{e(s.get("region", ""))} · 건물 {s.get("buildings", "?")}동</span><span class="go">부수러 가기 →</span></div></a>'
    for s in schools)
ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "WebSite", "name": "SMASH 고등학교", "alternateName": "우리 학교 부수기 게임", "url": URL, "inLanguage": "ko"},
    {"@type": "ItemList", "name": "SMASH 고등학교 학교 목록", "numberOfItems": len(schools),
     "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": URL + s["code"] + "/", "name": f'{s["name"]} 부수기 게임'} for i, s in enumerate(schools)]}]}
og = URL + schools[0]["code"] + "/og.png" if schools else ""
for k in ("__CARDS__", "__COUNT__", "__URL__", "__OG__", "__ISSUES__", "__REPO__", "<!--JSONLD-->"): assert k in tpl, k
page = (tpl.replace("__CARDS__", cards).replace("__COUNT__", str(len(schools))).replace("__URL__", URL).replace("__OG__", e(og))
        .replace("__ISSUES__", REPO + "/issues/new?title=학교+추가+요청").replace("__REPO__", REPO)
        .replace("<!--JSONLD-->", '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"))
(root / "site" / "index.html").write_text(page, encoding="utf-8")
print("site/index.html", len(page.encode()) // 1024, "KB,", len(schools), "schools")
