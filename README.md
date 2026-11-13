# motion-reel

서비스 홍보 영상이나 직접 만든 프로젝트의 사내 소개 영상을 15~30초 모션 그래픽(MP4)으로 만드는 에이전트 스킬이다.
Claude Code를 기준으로 만들었다.

요청 하나로 다음 순서를 끝까지 수행한다.

| 단계 | 하는 일 | 결과 파일 |
|---|---|---|
| 0. 요청 해석 | 길이(기본 30초), 대상 종류, 청중, 톤(차분·보통·강렬)을 정한다 | `brief.md` 상단 |
| 1. 리서치 | 외부 서비스는 공식 사이트와 공시 자료, 사용자 프로젝트는 저장소(README, 예제, `git log`)를 읽는다. 출처가 없는 수치는 쓰지 않는다 | `brief.md` |
| 2. 스토리보드 | 콘셉트 한 문장, 팔레트, 글꼴, 박자에 맞춘 샷 목록과 문구별 읽기 시간을 정한다 | `storyboard.md` |
| 3. 장면 구현 | 모든 프레임을 시간 `t`의 함수로 그리는 HTML/CSS/Canvas 장면을 만든다 | `index.html` |
| 4. 정지 프레임 검수 | 샷 중간과 전환 시점을 캡처해 잘림, 겹침, 대체 글꼴을 확인한다 | `stills/` |
| 5. 소리와 렌더 | 장면의 소리 큐로 음악과 효과음을 합성하고, 헤드리스 Chrome으로 60fps 프레임을 캡처해 인코딩한다 | `audio.wav`, `reel.mp4` |
| 6. 영상 검수 | 밀착 인화(0.5초 간격 프레임 모음), 검은 구간, 소리 크기를 확인한다 | `contact.png` |

결과물은 작업 디렉터리의 `reels/<대상>/`에 모인다.

## 설치

Claude Code에서 다음을 실행한다.

```
/plugin marketplace add JuwonHwang/motion-reel
/plugin install motion-reel@motion-reel
```

설치하면 스킬이 `motion-reel:motion-reel`로 등록된다. 저장소가 갱신되면 `/plugin marketplace update motion-reel`로 받는다.

## 필요한 것

- Node.js 18 이상: 렌더러(`scripts/render.mjs`). 처음 실행할 때 `playwright-core`를 설치한다
- Chrome, Chromium, Edge 중 하나: 프레임 캡처
- ffmpeg: 인코딩과 검수
- Python 3.9 이상: 음악과 효과음 합성(`scripts/sfx.py`, 표준 라이브러리만 사용)

## 사용 예

```
내가 만든 informative-slides 스킬을 회사 동료에게 소개하는 영상 만들어 줘. 저장소는 ~/Projects/informative-slide 야.
```

```
Figma를 홍보하는 15초 쇼릴 영상을 만들어 줘. 리서치해서 적절한 내용을 넣어 줘.
```

## 영상 규칙과 근거

수치 규칙은 방송, 자막, 접근성, 영상 배포 분야의 기준에서 가져왔다. 전체 목록과 출처, 근거 등급(원문 확인, 2차 자료, 관행)은 [`references/conventions.md`](skills/motion-reel/references/conventions.md)에 있다.

| 규칙 | 값 | 근거 |
|---|---|---|
| 글자 위치 | 화면 가장자리에서 5% 안쪽 (1080p 기준 가로 96px, 세로 54px) | EBU R 95 |
| 글자가 머무는 시간 | 한국어 `0.5초 + 음절 수 ÷ 12`, 영어 `0.5초 + 글자 수 ÷ 20`, 최소 0.84초 | Netflix 자막 기준의 읽기 속도와 최소 표시 시간 |
| 깜빡임 | 어떤 1초 구간에서든 3회 이하 | WCAG 2.3.1 |
| 소리 크기 | 기본 −16 LUFS, 방송용 `--lufs -23` | EBU R 128 (−16은 이 스킬이 정한 웹 재생용 값) |
| 인코딩 | 1920×1080, 60fps, H.264 High, BT.709, AAC 384kbps 48kHz | YouTube 권장 업로드 설정 |

## 렌더 시간

Apple Silicon Mac(고성능 코어 4개)에서 1920×1080 60fps, 모션 블러 2배로 측정했다.

| 영상 | 시간 |
|---|---|
| 15초 | 55초 |
| 30초 | 88초 |

렌더러는 Chrome DevTools Protocol의 압축 속도 우선 PNG 캡처(무손실)를 쓰고, 브라우저 4개가 프레임을 나눠 캡처한다.

## 한계

- 로고 파일을 주지 않으면 로고를 그리지 않고 이름을 글꼴로 조판한 워드마크로 대신한다.
- 제품 화면은 HTML/CSS로 단순화해 다시 그린 것이다. 스크린샷을 쓰지 않는다.
- 음악과 효과음은 합성음이다.
- 내레이션(음성)은 넣지 않는다.

## 라이선스

MIT License(`LICENSE`).
