# 업계 규칙과 근거

방송, 자막, 접근성, 영상 배포 분야에서 쓰는 규칙 중 짧은 모션 그래픽에 적용되는 것을 모았다. 항목마다 근거의 등급을 적는다.

- **표준**: 표준 기구나 플랫폼의 공식 문서 원문을 읽고 확인한 값
- **2차**: 원문을 읽지 못하고 2차 자료로만 확인한 값
- **관행**: 공식 기준이 없고 제작사 자료에서 범위로 나타나는 값
- **이 스킬의 값**: 위 근거를 바탕으로 이 스킬이 정한 값

확인일은 모두 2026-11-13이다.

## 1. 안전 영역

| 규칙 | 값 (1920×1080) | 등급 | 출처 |
|---|---|---|---|
| 그래픽 안전 영역(글자, 로고) | 상하좌우 각 5% 안쪽: 가로 96px, 세로 54px | 표준 | EBU R 95 "the graphics safe area is 5%, at the top, bottom and" 좌우 |
| 동작 안전 영역(중요한 움직임) | 상하좌우 각 3.5% 안쪽: 가로 67px, 세로 38px | 표준 | EBU R 95, 1080p 그림 4 (67px 정정 기록 포함) |
| SMPTE 안전 영역 | 동작 93%×93%, 제목 90%×90% | 2차 | SMPTE ST 2046-1 (NAB 요약으로 확인) |

적용: 모든 글자는 그래픽 안전 영역 안에 둔다. 배경, 입자, 전환 막대는 화면 끝까지 써도 된다.

## 2. 글자를 읽는 시간

자막 기준은 화면 글자를 읽는 속도에 대한 가장 구체적인 공개 기준이다.

| 규칙 | 값 | 등급 | 출처 |
|---|---|---|---|
| 한국어 읽기 속도(번역 자막, 성인) | 초당 12자 이하 | 표준 | Netflix Korean Timed Text Style Guide I.15 |
| 한국어 읽기 속도(청각장애인용 자막, 성인) | 초당 14자 이하 | 표준 | 같은 문서 II.3 |
| 한국어 한 줄 글자 수 | 16자. 라틴 문자, 공백, 문장부호는 0.5자 | 표준 | 같은 문서 I.2 |
| 영어 읽기 속도(성인) | 초당 20자 이하 | 표준 | Netflix English (USA) Timed Text Style Guide I.14 |
| 영어 한 줄 글자 수 | 42자 | 표준 | 같은 문서 I.2 |
| 한 덩어리 최소 표시 시간 | 5/6초(24fps 기준 20프레임) | 표준 | Netflix Timed Text Style Guide: General Requirements |
| 한 덩어리 최대 표시 시간 | 7초 | 표준 | 같은 문서 |
| 연속 문구 사이 간격 | 2프레임 또는 0.5초 이상 | 표준 | Netflix Subtitle Timing Guidelines |
| 영어 160~180 WPM, 단어당 0.3초 이상 | | 2차 | BBC Subtitle Guidelines (원문 접근 실패, 요약 자료로 확인) |

이 스킬의 값: 문구 하나가 완전히 보인 상태로 머무는 시간은 아래 둘 중 긴 쪽이다.
- 한국어 `0.5초 + 음절 수 ÷ 12`, 영어 `0.5초 + 글자 수 ÷ 20`. 0.5초는 문구가 나타난 것을 알아채는 시간으로 더한 값이다.
- 0.84초 (Netflix 최소 표시 시간)

한 줄은 한국어 16자, 영어 42자 이내로 쓴다. 자막과 달리 모션 그래픽 문구는 움직이면서 나타나므로, 진입 애니메이션 시간은 머무는 시간에 넣지 않는다.

## 3. 영상 길이와 글자 양

| 규칙 | 값 | 등급 | 출처 |
|---|---|---|---|
| 30초 설명 영상의 내레이션 분량 | 약 75단어(초당 약 2.5단어) | 관행 | 설명 영상 제작사 자료 다수(65~80단어 범위) |
| 끝 장면(로고, 슬로건) 유지 시간 | 2~3초, 행동 유도 문구가 있으면 더 길게 | 관행 | 광고 제작 자료 다수 |

이 스킬의 값: 내레이션 없이 화면 글자만 쓰는 영상이므로 내레이션 분량보다 적게 쓴다. 15초 영상은 한국어 60음절(영어 30단어), 30초 영상은 한국어 110음절(영어 55단어) 이내로 쓴다. 끝 장면은 15초 영상에서 2.5초, 30초 영상에서 4초 이상 두고, 그중 마지막 1.5초는 움직임 없이 정지한다.

## 4. 깜빡임과 반복 무늬

| 규칙 | 값 | 등급 | 출처 |
|---|---|---|---|
| 깜빡임 횟수 | 어떤 1초 구간에서도 3회 이하 | 표준 | WCAG 2.3.1 |
| 깜빡임의 정의 | 상대 휘도가 최대값의 10% 이상 바뀌었다가 돌아오는 한 쌍. 어두운 쪽 휘도가 0.80 미만일 때 | 표준 | WCAG 2.3.1 general flash threshold |
| 면적 예외 | 동시에 깜빡이는 면적이 시야 10도의 25% 이하. 1024×768 화면의 341×256px 사각형으로 추정하며, 1920×1080으로 환산하면 약 640×360px | 표준 (환산은 이 스킬의 계산) | WCAG 2.3.1 |
| 빨강 깜빡임 | 채도 높은 빨강의 반복 전환은 별도로 3회 이하 | 표준 | WCAG 2.3.1 red flash threshold |
| 방송 광고 | 영국 방송은 Harding 검사(깜빡임과 무늬 분석)를 통과해야 한다 | 2차 | Ofcom 지침(원문 접근 실패, Epilepsy Society 자료로 확인) |

적용: 화면 전체 플래시 프레임, 글리치, 빠른 색 반전을 1초에 3회 넘게 쓰지 않는다. 640×360px보다 큰 영역의 밝기 반전은 이 횟수에 들어간다. 빨강 면의 반복 깜빡임은 쓰지 않는다. 가는 줄무늬나 체크무늬가 화면을 크게 채우며 움직이는 장면도 피한다(WCAG가 예외로 둔 0.1도 미만의 미세 무늬는 제외).

## 5. 소리 크기

| 규칙 | 값 | 등급 | 출처 |
|---|---|---|---|
| 방송 프로그램 평균 소리 크기 | −23.0 LUFS, 생방송처럼 맞추기 어려운 경우 ±1.0 LU | 표준 | EBU R 128 v4 |
| 최대 순간 레벨(True Peak) | −1 dBTP 이하 | 표준 | EBU R 128 v4 |
| YouTube 목표 소리 크기 | 공식 문서에 LUFS 값이 없다. −14 LUFS라는 값은 2차 자료에만 있다 | 2차 | YouTube 권장 업로드 인코딩 설정 페이지에 소리 크기 항목 없음 |

LUFS는 사람이 느끼는 평균 소리 크기의 단위이다. 숫자가 0에 가까울수록 크다.

이 스킬의 값: 사내 공유와 웹 재생용으로 −16 LUFS, True Peak −1.5 dBTP로 맞춘다. 방송에 낼 영상이면 −23 LUFS로 바꾼다. 측정: 2026-11-13 이전에 만든 두 예시의 오디오는 정규화 전 −11.6 LUFS, −12.4 LUFS였다.

## 6. 인코딩

| 규칙 | 값 | 등급 | 출처 |
|---|---|---|---|
| 컨테이너, 코덱 | MP4, H.264 High Profile, CABAC, 4:2:0 | 표준 | YouTube 권장 업로드 인코딩 설정 |
| 프레임레이트 | 제작한 프레임레이트 그대로(24, 25, 30, 48, 50, 60) | 표준 | 같은 문서 |
| 1080p 비트레이트(SDR) | 24~30fps 8 Mbps, 48~60fps 12 Mbps | 표준 | 같은 문서 |
| 색 공간 | BT.709 | 표준 | 같은 문서 |
| 오디오 | AAC-LC, 48kHz, 스테레오 384 kbps | 표준 | 같은 문서 |

적용: `render.mjs`는 libx264(High Profile, yuv420p), CRF 16, BT.709 색 공간 표기, AAC 384 kbps 48kHz로 인코딩한다. CRF 16의 1080p60 결과는 위 권장 비트레이트보다 크다(측정: informative-slides 예시 37MB/15초 ≈ 19.6 Mbps). 업로드 용량 제한이 있으면 `--crf 20`으로 올린다.

## 7. 움직임의 시간

| 규칙 | 값 | 등급 | 출처 |
|---|---|---|---|
| UI 요소의 진입·퇴장 | 150~250ms | 2차 | Material Design, Atlassian 디자인 시스템 요약 자료 |
| 화면 전체 전환 | 300~500ms | 2차 | 같은 자료 |
| 강조 동작 | 400~700ms | 2차 | 같은 자료 |
| 100ms 미만의 움직임 | 움직임이 아니라 상태 변화로 보인다 | 2차 | 같은 자료 |

UI 기준은 사용자가 조작하는 화면을 위한 값이다. 영상의 시청자는 조작하지 않고 따라가기만 하므로, 이 스킬은 위 값보다 약간 긴 범위를 쓴다.

이 스킬의 값: 글자와 요소 진입 0.4~0.8초, 화면 전체 전환 0.5~0.9초, 제품 UI 재현 안의 버튼·토글 같은 작은 상태 변화 0.15~0.3초. 0.1초 미만의 이동은 쓰지 않는다(플래시 프레임은 예외).

## 8. 애니메이션 원칙

Frank Thomas와 Ollie Johnston의 *The Illusion of Life*(1981)가 정리한 12가지 원칙은 캐릭터 애니메이션에서 나왔지만, 모션 그래픽에도 적용된다. 이 스킬에서 쓰는 방식은 다음과 같다.

| 원칙 | 모션 그래픽에서의 적용 |
|---|---|
| 천천히 시작, 천천히 끝(slow in, slow out) | 선형 이동을 쓰지 않는다. `E.outCubic`, `E.inOutCubic`, `E.outExpo` 사용 |
| 예비 동작(anticipation) | 큰 이동 직전에 반대 방향으로 짧게(0.1~0.15초, 이동 거리의 5~10%) 움직인다 |
| 후속 동작과 겹침(follow-through, overlapping) | 묶음의 요소들이 동시에 멈추지 않게 0.03~0.08초씩 시차를 둔다(stagger) |
| 연출(staging) | 한 시점에 시선을 끄는 움직임은 하나만 둔다 |
| 호(arcs) | 위치 이동은 직선 대신 약한 곡선 경로로 움직인다 |
| 과장(exaggeration) | 크기나 위치의 넘침(overshoot)은 강렬 톤에서만 쓰고, 넘침 폭은 5% 이하로 둔다 |
| 타이밍(timing) | 무거운 요소는 길게, 가벼운 요소는 짧게 움직인다 |

등급: 원칙 목록은 관행이다. 오른쪽 열의 수치는 이 스킬의 값이다.

## 출처 목록

- EBU R 95, Safe areas for 16:9 television production: https://tech.ebu.ch/docs/r/r095.pdf
- EBU R 128 v4, Loudness normalisation and permitted maximum level of audio signals: https://tech.ebu.ch/docs/r/r128v4_0.pdf
- SMPTE ST 2046-1 요약(NAB): https://www.nab.org/xert/scitech/pdfs/tv031510.pdf
- Netflix Korean Timed Text Style Guide: https://partnerhelp.netflixstudios.com/hc/en-us/articles/216001127-Korean-Timed-Text-Style-Guide
- Netflix English (USA) Timed Text Style Guide: https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
- Netflix Timed Text Style Guide: General Requirements: https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617
- Netflix Subtitle Timing Guidelines: https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines
- BBC 자막 기준 요약: https://clevercast.com/bbc-subtitling-guidelines
- WCAG 2.1 Understanding SC 2.3.1: https://w3c.github.io/wcag21/understanding/three-flashes-or-below-threshold
- Harding 검사와 Ofcom: https://en.wikipedia.org/wiki/Harding_test , https://epilepsy.org.uk/?p=110779
- YouTube 권장 업로드 인코딩 설정: https://support.google.com/youtube/answer/1722171
- 설명 영상 분량: https://vidico.com/news/30-second-explainer-video/ , https://explain.ninja/30-second-video
- 끝 장면 유지 시간: https://www.brandvm.com/post/brand-slate-finishing-ai-ad-film
- UI 움직임 시간: https://uiux-atlas.pages.dev/lessons/motion/easing-and-timing , https://atlassian.design/foundations/motion/applying-motion
