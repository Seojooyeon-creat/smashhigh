# SMASH 남대전고

대전 남대전고등학교 캠퍼스를 3D로 부수는 브라우저 게임입니다. 학교와 관계없는 비공식 팬 게임이고, 학교 로고나 교표는 쓰지 않습니다.

[SMASH 대학교](https://hong-iron.github.io/SMASH/)의 원리(OpenStreetMap 건물 윤곽 + 층수 → 3D 박스 → 조각내기)를 보고 처음부터 새로 만든 고등학교 버전입니다. 원작 코드는 쓰지 않았습니다.

## 하는 법

- 건물을 누르면 고른 도구로 부숩니다. 떨어진 조각을 또 누르면 더 잘게 부서집니다.
- 도구는 여섯 가지, 숫자 키 1~6.
  - 폭탄: 던져서 넓게 날리고 땅에 떨어지면 구덩이를 팝니다.
  - 야구 배트: 거대한 배트로 쳐서 멀리 날립니다. 크기 ×0.5~×3. 70 m 넘게 날아가면 홈런.
  - 레이저: 화면을 끌어 선을 그으면 하늘이 어두워지며 충전한 뒤 빔이 선을 훑습니다. 톡 누르면 한 점.
  - 운석: 카메라가 운석을 따라가고 큰 구덩이가 생깁니다.
  - 지진: 규모 4.0~10.0. 4~5는 흔들리기만, 6~7은 일부 붕괴, 8 이상은 땅이 출렁이고 통째로 무너집니다.
  - 핵폭탄: 섬광, 슬로모션, 버섯구름. 반경 380 m 전부.
  - 운석·핵폭탄 연출 중 화면을 누르거나 Esc 를 누르면 건너뜁니다.
- 스타일 랭크 D → C → B → A → S → SS → SSS. 도구를 바꿔 가며 빠르게 부수면 배율이 오르고, 같은 도구만 쓰면 깎입니다. 공중 콤보, 붕괴 보너스.
- 땅을 계속 파면 흙 → 지각 → 맨틀 → 외핵 → 내핵. 아래 깊이 표시는 지구 기준 km 로 환산합니다.
- 되돌리기(Ctrl+Z / ⌘Z)는 한 단계씩, 전부 복구는 처음으로. 되감기 연출이 나옵니다.
- 공유: 점수·랭크·파괴율이 얹힌 결과 카드 이미지. 휴대폰은 공유 목록, PC 는 저장·링크 복사.
- 밤 (N): 창문에 불이 켜지고 별이 뜹니다.
- 조작: 끌기 돌리기, 오른쪽 끌기 옮기기, 휠 확대. 휴대폰은 한 손가락 옮기기, 두 손가락 돌리기·확대.

## 만든 방법

- three.js r160 (CDN), 소리는 Web Audio 합성. 의존성 설치 없음.
- 데이터: `tools/fetch.py` 가 Overpass 로 학교 경계 안팎의 건물·도로·녹지와 AWS Terrain Tiles 고도를 받고, `tools/build_campus.py` 가 미터 좌표의 `data/campus.json` 으로 바꿉니다.
  ```
  python3 tools/fetch.py way 30658725 raw 120          # 남대전고 OSM way, 주변 120 m
  python3 tools/build_campus.py raw data/campus.json config.json
  python3 tools/assemble.py                           # src/app.html + data + config → site/index.html
  ```
  `build_campus.py` 는 numpy, matplotlib 이 필요합니다.
- 층수는 OSM 에 없으면 넓이로 어림합니다. `config.json` 의 `levels` 에 `"way/ID": 층수` 로 덮어쓰고, `names` 로 건물 이름을 붙입니다. `look` 으로 건물별 벽·유리·지붕 색과 양식(stone/brick/glass/dorm)을 정할 수 있습니다.
- 건물은 OBB 격자로 잘라 InstancedMesh 하나로 그립니다. 물리는 직접 짠 간단한 것(중력, 땅·건물 위 착지, 지지 없는 칸 붕괴)입니다.
- `main` 에 push 하면 GitHub Actions 가 `site/` 를 GitHub Pages 에 올립니다.
- 확인용: 주소 뒤에 `?demo=bomb|bat|laser|meteor|quake|nuke&at=밀리초` 를 붙이면 그리기 전에 그 도구를 본관에 쓰고 그만큼 돌린 상태로 시작합니다. `&night`, `&clean`(UI 숨김), `&lite`(그림자 끔), `&fps` 는 없음.

## 데이터와 출처

- 학교 경계, 건물 윤곽, 도로, 녹지: © OpenStreetMap 기여자 (ODbL). `data/campus.json` 도 ODbL.
- 땅 높이: AWS Terrain Tiles (Mapzen terrarium, SRTM 30 m).
- 남대전고 부지 안 건물 6동, 바로 옆 청란여중·청란여고 건물 등 모두 16동.

## 아직 없는 것

- 학교 랭킹 서버(원작은 Supabase). 지금은 기기 안 최고 점수만 저장합니다.
- 카카오톡 공유 SDK.
- 브이월드 건물통합정보로 층수·지붕색 보강 (`VWORLD_KEY` 필요).
- 여러 학교를 모으는 허브 페이지.
