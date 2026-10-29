# src/app.html + data/campus.json + config.json → site/index.html
# usage: python3 tools/assemble.py
import html, json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
tpl = (root / "src" / "app.html").read_text(encoding="utf-8")
data = json.loads((root / "data" / "campus.json").read_text(encoding="utf-8"))
data["config"] = cfg
blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
page_title = f"{cfg['school']} 부수기 게임 | {cfg['campusName']} 3D | {cfg['title']}"
desc = cfg["description"] + ". 폭탄, 야구 배트, 레이저, 운석, 지진, 핵폭탄으로 건물을 무너뜨리고, 설치 없이 휴대폰과 PC 브라우저에서 무료로 할 수 있습니다."
for k in ("__DATA__", "__TITLE__", "__PAGE_TITLE__", "__DESC__", "__URL__", "__TAGLINE__"):
    assert k in tpl, k
e = lambda v: html.escape(v, quote=True)
page = (tpl.replace("__DATA__", blob).replace("__PAGE_TITLE__", e(page_title)).replace("__TITLE__", e(cfg["title"]))
        .replace("__DESC__", e(desc)).replace("__URL__", e(cfg["url"])).replace("__TAGLINE__", e(cfg["tagline"])))
(root / "site" / "index.html").write_text(page, encoding="utf-8")
print("site/index.html", len(page.encode()) // 1024, "KB")
