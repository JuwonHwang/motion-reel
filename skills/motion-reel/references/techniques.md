# 모션 기법 목록

`assets/template.html` 엔진의 헬퍼(`tw`, `inOut`, `spring`, `set`, `split`, `wipe`, `scramble`, `count`, `rng`, `noise1`)로 구현하는 기법이다. 모든 코드는 `update(lt, st)` 안에서 시각 `lt`만으로 상태를 계산한다. 장면마다 2~3개를 고르고, 영상 전체에서 같은 기법을 세 번 넘게 반복하지 않는다.

## 목차
1. 타이포그래피 — 글자 단위 진입, 마스크 라인 리빌, 해독, 가변 폰트, 대형 크롭 타이포
2. 전환 — 마스크 와이프, 매치 컷, 줌 스루, 색면 슬라이스, 스매시 컷
3. 형태 — 선 그리기, 도형 변형, 그리드 인스턴싱, 궤도
4. 데이터와 UI — 카운트업, 막대와 링 차트, 제품 UI 재현, 커서와 클릭
5. 공간 — CSS 3D 카메라, 패럴랙스 레이어, 카드 스택
6. 캔버스와 WebGL — 입자장, 궤적, 셰이더 배경
7. 후처리 — 모션 블러, 그레인, 색수차, 카메라 흔들림, 플래시 프레임

---

## 1. 타이포그래피

**글자 단위 진입 (stagger).** 가장 기본이지만 곡선과 간격이 결과를 정한다. `E.snap`이나 `E.outExpo`로 빠르게 들어와 오래 감속하게 하고, 간격은 0.02~0.05초로 둔다.
```js
st.chars.forEach((c, i) => {
  const p = tw(lt, 0.1 + i * 0.03, 0.8, E.snap);
  set(c, { y: lerp(120, 0, p), ry: lerp(-90, 0, p), o: p });
});
```

**마스크 라인 리빌.** 글자를 부모의 `overflow:hidden` 밖에서 밀어 올린다. 페이드 없이 날카로운 경계가 생긴다.
```html
<div class="line-mask"><div class="line">Ship faster.</div></div>
```
```js
// 줄 높이(px)만큼 아래에서 시작한다. 여러 줄이면 줄마다 0.08초씩 늦춘다.
st.lines.forEach((l, i) => set(l, { y: lerp(l.offsetHeight * 1.1, 0, tw(lt, i * .08, .7, E.snap)) }));
```

**해독 (scramble).** 코드, 데이터, 보안, AI 같은 주제에 맞는다. `scramble(text, p)`를 `textContent`에 넣는다. 고정폭 글꼴에서 글자 폭이 흔들리지 않는다.

**가변 폰트 축.** `font-variation-settings: 'wght' ${lerp(100, 900, p)}` 로 굵기를 시간에 따라 바꾼다. Pretendard Variable, Inter, Roboto Flex 가 지원한다.

**대형 크롭 타이포.** 화면보다 큰 글자(600~1200px)를 일부만 보이게 두고 천천히 스케일한다. 단어 사이를 카메라가 지나가는 전환의 출발점으로 쓴다.

**외곽선과 채움 교차.** `-webkit-text-stroke: 2px var(--fg); color: transparent` 인 사본 위에 채움 사본을 `clip-path: wipe(p)`로 덮는다.

## 2. 전환

전환은 앞 장면의 요소가 다음 장면의 요소가 되도록 연결할 때 가장 강하다. 컷 시각은 반드시 박자(`beat(n)`)에 맞춘다.

**마스크 와이프.** 다음 장면 레이어에 `clip: wipe(p, 'left')`. 원형은 `circle(${lerp(0, 150, p)}% at 50% 50%)`. 대각선은 `polygon()`.

**매치 컷.** 앞 장면의 원(예: 버튼, 점)이 다음 장면의 원(예: 지구, 로고 마크)과 같은 위치와 크기에서 이어진다. 두 장면을 0.05초 겹치고 같은 좌표를 쓴다.

**줌 스루.** 글자 `O`나 UI 창 안으로 `s: lerp(1, 40, E.inExpo(p))`로 확대해 들어가고, 그 안쪽 색이 다음 장면 배경이 된다. 확대 기준점은 `transform-origin`을 대상 중심 좌표로 둔다.

**색면 슬라이스.** 3~5개의 색 막대가 시차를 두고 화면을 가로지른 뒤, 마지막 막대 뒤에서 다음 장면이 드러난다.
```js
st.bars.forEach((b, i) => {
  const pin = tw(lt, i * .05, .35, E.inOutExpo), pout = tw(lt, .3 + i * .05, .35, E.inOutExpo);
  set(b, { x: lerp(-W, 0, pin) + lerp(0, W, pout) });
});
```

**스매시 컷.** 정적인 장면에서 강한 장면으로 1프레임 플래시(흰 레이어 opacity 1→0, 0.08초)와 함께 끊는다. 소리 큐 `impact`를 같은 시각에 둔다.

## 3. 형태

**선 그리기.** SVG 경로의 `stroke-dasharray = 길이`, `stroke-dashoffset = 길이 * (1 - p)`. 길이는 `path.getTotalLength()`로 build 시점에 구한다. 연결, 경로, 성장 같은 내용을 그릴 때 쓴다.

**도형 변형.** 같은 꼭짓점 수를 가진 두 `polygon` 좌표를 `lerp`로 보간해 `clip-path`나 SVG `points`에 넣는다. 둥근 사각형 ↔ 원은 `border-radius`를 보간한다.

**그리드 인스턴싱.** 같은 요소를 8×5, 16×9 격자로 복제하고 중심으로부터의 거리 `d`로 지연을 준다. 물결처럼 퍼지는 진입이 된다.
```js
const d = Math.hypot(col - cx, row - cy); const p = tw(lt, d * .04, .6, E.outBack);
```

**궤도.** 위성 요소를 `x = R cos(ωt + φ)`, `y = r sin(ωt + φ)`로 돌리고 `z`에 따라 스케일과 밝기를 바꾸면 3D 궤도로 보인다. 통합, 생태계, 연결된 서비스를 보일 때 쓴다.

## 4. 데이터와 UI

서비스 홍보 영상에서 신뢰를 주는 부분이다. 숫자와 화면은 리서치에서 확인한 사실만 쓴다.

**카운트업.** `count(E.outExpo(p), 12000000, { suffix: '+' })`. 고정폭 숫자를 위해 `font-variant-numeric: tabular-nums`.

**막대·링 차트.** 막대는 `sy` 스케일(원점 아래), 링은 SVG 원의 `stroke-dashoffset`. 값 라벨은 막대 끝을 따라 움직인다.

**제품 UI 재현.** 서비스의 실제 화면을 단순화해 HTML/CSS로 다시 그린다(창 틀, 사이드바, 카드, 입력창, 채팅 말풍선, 코드 블록). 스크린샷을 쓰지 않으므로 모든 요소를 따로 움직일 수 있다. 회색 막대(skeleton)로 본문을 대신하고, 영상에서 강조할 한 요소만 실제 텍스트와 강조색으로 둔다.

**커서와 클릭.** SVG 커서를 베지어 경로로 이동시키고(`E.inOutCubic`), 도착 시 버튼을 `s: 1 - .06 * inOut(...)`으로 눌렀다 놓고, 원형 파문을 퍼뜨린다. 소리 큐 `tick`을 클릭 시각에 둔다.

**타이핑.** `text.slice(0, Math.floor(p * text.length))` 와 깜빡이는 캐럿(`Math.floor(lt * 2) % 2`). 소리 큐 `type`.

## 5. 공간

**CSS 3D 카메라.** 장면 루트에 `perspective: 1600px`, 내부 그룹에 `transform-style: preserve-3d`를 두고, 그룹 전체를 `rx`, `ry`, `z`로 움직인다. 카드와 UI 패널을 서로 다른 `z`에 두면 카메라 이동만으로 깊이가 보인다.

**3D 플립.** 카드 앞면과 뒷면을 같은 부모 안에 겹치고 `backface-visibility: hidden`을 준다. 뒷면은 `set(back, { ry: angle, post: 'rotateY(180deg)' })`, 앞면은 `set(front, { ry: angle })`. 부모에 `transform-style: preserve-3d`, 원근은 카드의 직계 부모에 `perspective: 1600px`로 둔다. 조상 중 `overflow: hidden`, `filter`, `opacity < 1`, `clip-path`가 있는 요소는 3D를 평면으로 만든다. 마스크가 필요하면 3D 그룹 바깥 요소에 건다.

**패럴랙스.** 레이어마다 이동량을 `z`에 반비례하게 둔다. 전경 1.0, 중경 0.5, 배경 0.2.

**카드 스택.** 여러 기능 카드를 `z` 간격 200px로 쌓고, 카메라가 앞으로 이동하며 카드를 하나씩 통과한다. 기능 3개를 2초 안에 보일 때 쓴다.

## 6. 캔버스와 WebGL

**입자장.** `rng(seed)`로 build 때 입자 초기값을 만들고, update 에서 `pos = start + vel * lt + noise1(...)`처럼 시각의 함수로 계산한다. 이전 프레임 상태를 누적하지 않는다. 입자가 모여 로고나 글자가 되는 효과는 오프스크린 캔버스에 글자를 그려 픽셀 좌표를 목표점으로 샘플링한다.
```js
// build
const off = new OffscreenCanvas(W, H), o = off.getContext('2d');
o.font = '900 300px Inter Tight'; o.fillText('NAME', 400, 600);
const data = o.getImageData(0, 0, W, H).data, pts = [];
for (let y = 0; y < H; y += 8) for (let x = 0; x < W; x += 8) if (data[(y * W + x) * 4 + 3] > 128) pts.push([x, y]);
// update: p = tw(lt, delay_i, 1.2, E.inOutExpo); pos = lerp(scatter_i, pts[i], p)
```
오프스크린 캔버스에 웹 글꼴을 쓰려면 `document.fonts.ready` 이후에 build 해야 한다. 장면 정의를 `ready.then(...)` 안에서 하거나 첫 update 에서 지연 생성한다.

입자가 모인 뒤 선명한 글자로 바꿀 때, DOM 글자를 따로 띄우면 기준선과 자간이 캔버스 글자와 몇 px 어긋난다. 최종 글자도 같은 캔버스에 같은 `font`, `textAlign`, `textBaseline`, 좌표로 `fillText` 해서 입자를 페이드아웃하며 교체한다. 캔버스의 `ctx.letterSpacing`은 CSS `letter-spacing`과 같은 값으로 맞춘다.

**궤적.** 이전 프레임을 지우지 않는 방식은 비결정적이다. 대신 각 입자의 최근 위치 N개를 `lt - k*dt`로 다시 계산해 선으로 잇는다.

**셰이더 배경.** three.js(`https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js`)나 순수 WebGL로 그라데이션 메시, 노이즈 필드, 빛 번짐을 그린다. 유니폼 `uTime = t`로만 움직인다. `preserveDrawingBuffer: true`로 컨텍스트를 만들고 renderFrame 안에서 `renderer.render()`를 동기 호출한다.

## 7. 후처리

**모션 블러.** 렌더러 옵션 `--blur 2~4`가 하위 프레임을 평균한다. 빠른 이동과 회전이 많은 영상일수록 효과가 크다. 장면 안에서 방향성 블러를 더 주려면 이동 속도에 비례해 `blur` 필터를 1~6px 준다.

**그레인과 비네트.** 템플릿에 포함되어 있다. 밝은 배경에서는 `#grain` opacity 를 0.05로 낮춘다.

**색수차.** 같은 텍스트 사본 3개를 `mix-blend-mode: screen`으로 겹치고 빨강, 초록, 파랑으로 칠한 뒤 x 방향으로 ±(2~12)px 벌렸다가 0으로 모은다. 전환 순간 0.1~0.2초만 쓴다.

**카메라 흔들림.** 템플릿의 `camera(t)`에 임팩트 시각마다 `noise1` 기반 흔들림을 추가한다. 진폭 4~12px, 0.3~0.6초 감쇠.

**줌 펀치.** 박자마다 `s: 1 + .03 * (1 - tw(lt, beatTime, .25, E.outCubic))`. 음악의 킥과 맞추면 화면이 박자에 반응하는 것으로 보인다.

**플래시 프레임.** 흰색 또는 강조색 전면 레이어를 2~5프레임 동안 opacity 1에서 0으로 내린다.
