# raw/ 의 OSM·고도 자료를 게임용 로컬 미터 좌표 JSON으로 바꿉니다. (numpy, matplotlib 필요)
# usage: python3 tools/build_campus.py <raw_dir> <out.json> [config.json]
import glob, json, math, os, random, sys
import numpy as np
import matplotlib.image as mimg

RAW, OUT = sys.argv[1], sys.argv[2]
cfg = json.load(open(sys.argv[3], encoding="utf-8")) if len(sys.argv) > 3 else {}
meta = json.load(open(os.path.join(RAW, "meta.json")))
S_, W_, N_, E_ = meta["bbox"]; LAT0, LON0 = meta["center"]
phi = math.radians(LAT0)
MLAT = 111132.92 - 559.82 * math.cos(2 * phi) + 1.175 * math.cos(4 * phi)
MLON = 111412.84 * math.cos(phi) - 93.5 * math.cos(3 * phi)
def proj(lon, lat): return (round((lon - LON0) * MLON, 1), round((LAT0 - lat) * MLAT, 1))   # x east, z south
X0, Z0 = proj(W_, N_); X1, Z1 = proj(E_, S_)
STEP = 2.5

# ---- terrain: terrarium tiles → metre grid
tiles = [tuple(map(int, os.path.basename(f)[:-4].split("_"))) + (f,) for f in glob.glob(os.path.join(RAW, "dem", "*.png"))]
ZL = tiles[0][0]; TX0 = min(t[1] for t in tiles); TY0 = min(t[2] for t in tiles)
cols = max(t[1] for t in tiles) - TX0 + 1; rows = max(t[2] for t in tiles) - TY0 + 1
mos = np.zeros((rows * 256, cols * 256))
for _, tx, ty, f in tiles:
    a = (mimg.imread(f)[:, :, :3] * 255).round()
    mos[(ty - TY0) * 256:(ty - TY0 + 1) * 256, (tx - TX0) * 256:(tx - TX0 + 1) * 256] = a[:, :, 0] * 256 + a[:, :, 1] + a[:, :, 2] / 256 - 32768
def dem(lon, lat):
    n = 2 ** ZL * 256
    gx = (lon + 180) / 360 * n - TX0 * 256 - 0.5
    gy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n - TY0 * 256 - 0.5
    gx = min(max(gx, 0), mos.shape[1] - 1.001); gy = min(max(gy, 0), mos.shape[0] - 1.001)
    x0, y0 = int(gx), int(gy); fx, fy = gx - x0, gy - y0
    v = mos[y0:y0 + 2, x0:x0 + 2]
    return v[0, 0] * (1 - fx) * (1 - fy) + v[0, 1] * fx * (1 - fy) + v[1, 0] * (1 - fx) * fy + v[1, 1] * fx * fy
nx = int(round((X1 - X0) / STEP)) + 1; nz = int(round((Z1 - Z0) / STEP)) + 1
grid = np.array([[dem(LON0 + (X0 + j * STEP) / MLON, LAT0 - (Z0 + i * STEP) / MLAT) for j in range(nx)] for i in range(nz)])
for _ in range(2):   # 30 m SRTM 을 2.5 m 격자로 늘렸으니 두 번 부드럽게
    g2 = grid.copy()
    g2[1:-1, 1:-1] = sum(grid[1 + di:nz - 1 + di, 1 + dj:nx - 1 + dj] for di in (-1, 0, 1) for dj in (-1, 0, 1)) / 9
    grid = g2
base = float(np.median(grid)); grid -= base   # 캠퍼스 중앙 높이를 0 근처로

# ---- geometry helpers
def ring_of(el):
    if el["type"] == "way": return [proj(p["lon"], p["lat"]) for p in el["geometry"]]
    outer = [m for m in el.get("members", []) if m.get("role") == "outer" and "geometry" in m]
    return [proj(p["lon"], p["lat"]) for p in outer[0]["geometry"]] if outer else []
def area(r): return abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))) / 2
def inside(pt, poly):
    x, y = pt; c = False
    for k in range(len(poly)):
        x1, y1 = poly[k]; x2, y2 = poly[k - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
def centroid(r): return (sum(p[0] for p in r) / len(r), sum(p[1] for p in r) / len(r))
def dedupe(r):
    out = [r[0]]
    for p in r[1:]:
        if p != out[-1]: out.append(p)
    if len(out) > 1 and out[0] == out[-1]: out.pop()
    return out

campus_el = json.load(open(os.path.join(RAW, "campus.json")))["elements"][0]
campus = dedupe(ring_of(campus_el))
feats = json.load(open(os.path.join(RAW, "area.json")))["elements"]

# ---- buildings
# ponytail: 층수 없으면 넓이로 어림. 정확히 하려면 config.json "levels": {"way/ID": n} 로 덮어쓰기
over = cfg.get("levels", {})
names = cfg.get("names", {})
def guess_levels(r, tags):
    a = area(r)
    if tags.get("building") in ("school", "university", "yes"):
        if a > 700: return 4           # 본관·교사동
        if a > 450: return 3
        if a > 250: return 2
        return 1
    return 3 if a > 300 else 2
buildings = []
for el in feats:
    if "building" not in el.get("tags", {}): continue
    r = dedupe(ring_of(el))
    if len(r) < 3: continue
    t = el["tags"]; bid = f'{el["type"]}/{el["id"]}'
    lv = int(over.get(bid) or t.get("building:levels") or guess_levels(r, t))
    h = float(t["height"]) if t.get("height", "").replace(".", "").isdigit() else lv * 3.4 + 0.6
    c = centroid(r)
    buildings.append({"id": bid, "n": names.get(bid) or t.get("name", ""), "kind": t["building"], "lv": lv, "h": round(h, 1),
                      "campus": inside(c, campus), "o": r, "a": round(area(r))})
buildings.sort(key=lambda b: -b["a"])

# ---- roads, lands
ROADW = {"primary": 14, "secondary": 11, "tertiary": 9, "residential": 6, "unclassified": 6, "service": 4.5, "living_street": 5,
         "footway": 2, "path": 1.8, "steps": 2, "track": 3, "pedestrian": 5, "cycleway": 2.5}
roads = [{"k": el["tags"]["highway"], "w": ROADW.get(el["tags"]["highway"], 5), "n": el["tags"].get("name", ""),
          "p": [proj(p["lon"], p["lat"]) for p in el["geometry"]]}
         for el in feats if el["type"] == "way" and "highway" in el.get("tags", {}) and el["tags"]["highway"] in ROADW]
LANDK = {("natural", "wood"): "wood", ("landuse", "forest"): "wood", ("landuse", "grass"): "grass", ("leisure", "park"): "grass",
         ("leisure", "pitch"): "pitch", ("leisure", "track"): "pitch", ("leisure", "playground"): "grass", ("natural", "water"): "water",
         ("landuse", "residential"): "urban", ("amenity", "parking"): "paved", ("amenity", "school"): "school"}
def clip_rect(r):   # Sutherland–Hodgman 사각 클리핑: 보문산처럼 범위 밖까지 뻗은 폴리곤을 자름
    for axis, lim, keep in ((0, X0, lambda p: p[0] >= X0), (0, X1, lambda p: p[0] <= X1), (1, Z0, lambda p: p[1] >= Z0), (1, Z1, lambda p: p[1] <= Z1)):
        out = []
        for i in range(len(r)):
            a, b = r[i - 1], r[i]; ka, kb = keep(a), keep(b)
            if ka != kb:
                t = (lim - a[axis]) / (b[axis] - a[axis]); out.append((round(a[0] + (b[0] - a[0]) * t, 1), round(a[1] + (b[1] - a[1]) * t, 1)))
            if kb: out.append(b)
        r = out
        if len(r) < 3: return []
    return r
lands = []
for el in feats:
    t = el.get("tags", {})
    for (k, v), kind in LANDK.items():
        if t.get(k) == v:
            r = clip_rect(dedupe(ring_of(el)))
            if len(r) >= 3: lands.append({"k": kind, "r": r, "n": t.get("name", "")})

# ---- trees: 숲 안에 촘촘히, 캠퍼스 가장자리에 듬성듬성 (건물·도로 위는 피함)
rng = random.Random(7)
def clear(pt):
    for b in buildings:
        if inside(pt, b["o"]): return False
    for rd in roads:
        for i in range(1, len(rd["p"])):
            (ax, az), (bx, bz) = rd["p"][i - 1], rd["p"][i]
            dx, dz = bx - ax, bz - az; L = dx * dx + dz * dz or 1
            u = min(1, max(0, ((pt[0] - ax) * dx + (pt[1] - az) * dz) / L))
            if math.hypot(pt[0] - ax - u * dx, pt[1] - az - u * dz) < rd["w"] / 2 + 1.5: return False
    return True
trees = []
for l in lands:
    if l["k"] != "wood": continue
    xs = [p[0] for p in l["r"]]; zs = [p[1] for p in l["r"]]
    for _ in range(min(int(area(l["r"]) / 40), 1500)):
        p = (rng.uniform(min(xs), max(xs)), rng.uniform(min(zs), max(zs)))
        if inside(p, l["r"]) and clear(p): trees.append([round(p[0], 1), round(p[1], 1), round(rng.uniform(0.8, 1.3), 2)])
for i in range(len(campus)):   # 담장 따라 가로수
    (ax, az), (bx, bz) = campus[i - 1], campus[i]
    n = int(math.hypot(bx - ax, bz - az) / 9)
    for k in range(n):
        u = (k + 0.5) / n; p = (ax + (bx - ax) * u + rng.uniform(-1, 1), az + (bz - az) * u + rng.uniform(-1, 1))
        if clear(p) and rng.random() < 0.7: trees.append([round(p[0], 1), round(p[1], 1), round(rng.uniform(0.8, 1.2), 2)])

out = {"meta": {"lat": LAT0, "lon": LON0, "base": round(base, 1), "name": campus_el.get("tags", {}).get("name", "")},
       "terrain": {"x0": X0, "z0": Z0, "step": STEP, "nx": nx, "nz": nz, "h": [round(float(v), 1) for v in grid.ravel()]},
       "campus": campus, "buildings": buildings, "roads": roads, "lands": lands, "trees": trees}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"{OUT}: {len(buildings)} buildings ({sum(b['campus'] for b in buildings)} on campus), {len(roads)} roads, {len(lands)} lands, "
      f"{len(trees)} trees, terrain {nx}x{nz} range {grid.min():.1f}..{grid.max():.1f} m, {os.path.getsize(OUT)//1024} KB")
