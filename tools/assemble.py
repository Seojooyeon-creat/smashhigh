# schools/<code>/{config.json,campus.json,og.png} + src/app.html → site/<code>/index.html
# usage: python3 tools/assemble.py <code> [<code> ...]   (인자 없으면 schools/ 전부)
import html, json, pathlib, shutil, sys
root = pathlib.Path(__file__).resolve().parent.parent
tpl = (root / "src" / "app.html").read_text(encoding="utf-8")
codes = sys.argv[1:] or sorted(p.name for p in (root / "schools").iterdir() if (p / "config.json").exists())
for code in codes:
    sd = root / "schools" / code
    cfg = json.loads((sd / "config.json").read_text(encoding="utf-8"))
    data = json.loads((sd / "campus.json").read_text(encoding="utf-8")); data["config"] = cfg
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page_title = f"{cfg['school']} 부수기 게임 | {cfg['campusName']} 3D | {cfg['title']}"
    desc = cfg["description"] + ". 폭탄, 야구 배트, 레이저, 운석, 지진, 핵폭탄으로 건물을 무너뜨리고, 설치 없이 휴대폰과 PC 브라우저에서 무료로 할 수 있습니다."
    e = lambda v: html.escape(v, quote=True)
    page = (tpl.replace("__DATA__", blob).replace("__PAGE_TITLE__", e(page_title)).replace("__TITLE__", e(cfg["title"]))
            .replace("__DESC__", e(desc)).replace("__URL__", e(cfg["url"])).replace("__TAGLINE__", e(cfg["tagline"])).replace("__HUB__", e(cfg.get("hub", ""))))
    out = root / "site" / code; out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    if (sd / "og.png").exists(): shutil.copy(sd / "og.png", out / "og.png")
    print(f"site/{code}/index.html", len(page.encode()) // 1024, "KB")
