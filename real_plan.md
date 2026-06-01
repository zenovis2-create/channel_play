# Real Plan: Mac Studio + gdx1 기반 Unity 게임쇼 MVP 제작 계획

작성일: 2026-06-01
기준 문서: `master_plan.md`
계획 모드: gdx1 / ASUS GX10 사용 가능 전제. 현재 접속 단절은 운영 리스크로만 취급.

## 0. 현재 검증된 사실

### 0.1 로컬 제작 머신

현재 로컬 머신은 Mac Studio M2 Ultra 64GB로 확인됨.

- OS: macOS 26.4.1
- Architecture: arm64
- CPU: Apple M2 Ultra
- Memory: 64GB
- 작업 볼륨: `/Volumes/AI2`
- 작업 볼륨 여유 공간: 약 1.0TiB
- 현재 작업 폴더: `/Volumes/AI2/channel_play`

현재 작업 폴더 상태:

- `master_plan.md` 있음
- `real_plan.md`는 이 문서로 새로 생성
- 아직 Git 저장소 아님
- 아직 Unity 프로젝트 없음

설치 확인된 로컬 도구:

- Git: 있음
- GitHub CLI: 있음
- ffmpeg: 있음
- Docker CLI: 있음

현재 확인되지 않았거나 PATH/Applications에서 찾지 못한 도구:

- Unity Hub
- Unity Editor
- Git LFS
- Blender
- OBS
- VS Code CLI

### 0.2 gdx1 / ASUS GX10 원격 머신

사용자가 말한 `gdx-1`이라는 SSH 호스트명은 현재 해석되지 않음.

검증 결과:

- `ssh gdx-1`: hostname resolve 실패
- Tailscale에는 `gdx1` 호스트가 있음
- Tailscale IP: `100.78.48.61`
- Tailscale OS: Linux
- Tailscale 상태: online=true
- Tailscale SSH host key: 0개
- `ssh gdx1`: port 22 timeout
- `tailscale ping gdx1`: no reply

판정:

- gdx1은 Tailscale 장치 목록에는 있음.
- 현재 시점에는 SSH/핑이 실패했지만, 이 문서는 gdx1 복구 후 사용할 수 있다는 전제로 설계함.
- 단, 모든 원격 작업은 Mac Studio 단독 fallback을 유지해야 함.
- `gdx-1` 표기는 별칭으로만 취급하고, 스크립트/문서의 표준 호스트명은 `gdx1`로 둠.

### 0.3 ASUS GX10 공개 스펙 기준

ASUS 공식 사양 기준의 ASUS Ascent GX10:

- OS: Ubuntu Linux
- CPU: ARM v9.2-A CPU (GB10)
- GPU: NVIDIA Blackwell GPU (GB10, integrated)
- Memory: 128GB LPDDR5x unified system memory
- Storage: 1TB/2TB PCIe 4.0 NVMe 또는 4TB PCIe 5.0 NVMe 옵션
- Network: Wi-Fi 7, Bluetooth 5.4, 10G LAN, NVIDIA ConnectX-7 SmartNIC
- Power: 240W adapter

이 스펙 기준으로 GX10은 Unity Editor 본진이 아니라 Linux 서버/봇/자동화/AI 보조 워커로 쓰는 것이 맞음.

## 1. 실제 제작 전략

이 프로젝트는 처음부터 대형 온라인 게임으로 만들면 실패 확률이 높음.
`master_plan.md`의 핵심 목표에 맞춰, 먼저 "촬영 가능한 작은 게임쇼 세트장"을 완성한다.

현실적인 1차 목표:

- 4~8명 접속
- 작은 3D 맵 1개
- 운영자 1명
- 포인트 지급/차감
- 상점 구매
- 아이템 3개
- 제한시간
- 참가자 상태 표시
- OBS 녹화 가능한 화면
- 게임 로그 저장

기술 방향:

- Unity Editor 작업은 Mac Studio에서 수행
- Linux headless server는 gdx1을 1차 실행 목표로 설계
- Mac Studio는 Editor, 클라이언트 빌드, OBS, 영상 작업 담당
- gdx1은 dedicated server, bot load test, 장시간 soak test, 로그 수집 담당
- gdx1이 잠시 끊겨도 Mac Studio에서 Host/Client fallback 테스트 가능해야 함
- 대규모 클라우드/Unity Multiplay는 파일럿 촬영 성공 뒤 검토

## 2. 머신별 역할 분담

### 2.1 Mac Studio M2 Ultra

주 역할: 제작 본진.

담당:

- Unity Editor 실행
- 씬/프리팹/ScriptableObject 제작
- 로컬 플레이 테스트
- macOS 클라이언트 빌드
- Linux headless server 빌드 생성
- OBS 화면 구성
- 영상 녹화/편집 전처리
- Git 저장소 관리
- 디자인/밸런스 문서 업데이트

Mac Studio에 먼저 설치할 것:

- Unity Hub
- Unity 6 LTS 또는 현재 Unity LTS
- Git LFS
- OBS
- Blender
- Rider 또는 VS Code

### 2.2 gdx1 / ASUS GX10

주 역할: Linux 서버/검증/AI 보조 워커.

gdx1 담당:

- Linux headless dedicated server 실행
- 4~8명 bot 접속 테스트
- 장시간 soak test
- 네트워크 지연/재접속 테스트
- 자동 빌드 검증
- 서버 로그/게임 로그 저장
- Unity 로그/네트워크 로그 분석
- 로컬 LLM/AI 에이전트 보조 작업
- 반복 빌드/테스트 작업 분산
- 추후 2대 이상 클라이언트 테스트의 기준 서버

초기에는 gdx1을 Unity Editor 머신으로 쓰지 않는다.
Unity Editor는 Mac Studio에 두고, gdx1은 실행/검증/서버 역할로 분리한다.

GX10은 Ubuntu ARM + NVIDIA GB10 기반이므로, Unity Editor 호환/생태계보다 서버 실행, 자동화, AI 추론, 테스트 워커 역할이 더 안전하다.

## 3. gdx1 연결 복구 체크리스트

설계는 gdx1 사용 가능 전제다. 다만 현재 연결이 끊긴 상태라 아래 복구 확인이 필요함.

### 3.1 네이밍 정리

현재 확인된 이름은 `gdx1`이고, `gdx-1`은 없음.

선택:

- 표준 이름을 `gdx1`로 통일
- 또는 로컬 SSH config에 `gdx-1` alias 추가

권장:

- 내부 문서와 스크립트에서는 `gdx1` 사용
- 사용자가 원하면 `gdx-1` alias만 추가

### 3.2 SSH 접속 복구

필수 확인:

- gdx1 전원 켜짐
- gdx1 인터넷 연결 정상
- Tailscale 로그인 정상
- SSH server 실행 중
- Linux 방화벽에서 22번 허용
- Tailscale ACL에서 SSH/TCP 허용
- `zenovis1@100.78.48.61` 접속 가능

목표 상태:

- `ssh gdx1 hostname` 성공
- `ssh gdx1 nvidia-smi` 또는 GPU 확인 명령 성공
- `ssh gdx1 docker --version` 성공

### 3.3 워커 디렉터리

gdx1 접속 복구 후 생성할 표준 경로:

- `~/channel_play`
- `~/channel_play/builds`
- `~/channel_play/logs`
- `~/channel_play/artifacts`

## 4. Unity 기술 스택

### 4.1 Unity 버전

권장:

- Unity 6 LTS 또는 설치 시점의 최신 LTS
- Apple Silicon 네이티브 Editor

이유:

- Mac Studio M2 Ultra에서 Editor/빌드 속도 유리
- MVP 기간 동안 버전 변동 리스크를 줄여야 함
- 패키지 호환성과 장기 유지보수에 LTS가 유리

### 4.2 렌더링

권장:

- URP
- 낮은 폴리곤/명확한 색상 중심
- 폐교 맵은 분위기보다 가시성 우선

MVP에서는 그래픽 품질보다 다음이 중요함:

- 참가자 식별
- 팀 색상
- 이름표 가독성
- 아이템 사용 상태
- 운영자 관전 시야
- 방송 화면 가독성

### 4.3 멀티플레이

1차 권장:

- Netcode for GameObjects
- Unity Transport
- Host/Client 모드로 먼저 검증
- 이후 Dedicated Server 빌드 추가

서버 권한 원칙:

- 포인트는 서버만 변경
- 아이템 지급/사용 판정은 서버만 확정
- 미션 완료는 서버 검증
- 상점 구매는 서버 검증
- 게임 타이머는 서버 기준
- 클라이언트는 요청만 보냄

### 4.4 운영자 권한

MVP 운영자는 일반 참가자와 다른 권한을 가진 특수 클라이언트로 시작한다.

운영자 기능:

- 참가자 목록 보기
- 참가자 위치 보기
- 포인트 지급/차감
- 아이템 지급
- 팀 변경
- 전체 공지
- 타이머 시작/정지
- 게임 종료
- 관전 카메라 이동
- 로그 보기

보안은 초기에는 단순하게:

- 개발/파일럿: 운영자 전용 빌드 또는 로컬 비밀번호
- 공개 테스트 전: 서버 인증 토큰 도입

## 5. Unity 프로젝트 구조

권장 폴더:

```text
Assets/
  _Project/
    Art/
    Audio/
    Materials/
    Prefabs/
    Scenes/
    ScriptableObjects/
    Scripts/
      Core/
      Networking/
      Player/
      Operator/
      Points/
      Shop/
      Items/
      Missions/
      UI/
      Logging/
    Tests/
      EditMode/
      PlayMode/
```

씬 구조:

- `Boot`
- `MainMenu`
- `Lobby`
- `School_MVP`
- `OperatorView`
- `OverlayTest`

핵심 프리팹:

- `Player`
- `OperatorCamera`
- `ShopTerminal`
- `MissionTerminal`
- `ExitDoor`
- `ItemPickup`
- `ScoreboardUI`
- `GameTimerUI`
- `NameplateUI`

## 6. 아키텍처 원칙

`agency-unity-architect` 기준으로 적용할 원칙:

- God Class 금지
- 모든 시스템은 단일 책임
- 씬 오브젝트에 영구 데이터 저장 금지
- 설정값은 ScriptableObject로 분리
- 프리팹은 씬 의존성 없이 동작
- 포인트/상점/아이템/미션은 서버 권한 시스템으로 분리
- UI는 게임 상태를 직접 수정하지 않고 요청 이벤트만 보냄

핵심 시스템:

- `GameSessionSystem`
- `PlayerRegistry`
- `PointSystem`
- `ShopSystem`
- `ItemSystem`
- `MissionSystem`
- `OperatorCommandSystem`
- `GameTimerSystem`
- `GameLogSystem`
- `BroadcastOverlaySystem`

## 7. master_plan 기반 MVP 구현 순서

### 7.1 0단계: 제작 환경 준비

목표:

- Unity 프로젝트 생성 전 기반 정리

작업:

- Git 저장소 생성
- Git LFS 설정
- Unity Hub/Editor 설치
- Unity 프로젝트 생성
- `.gitignore` / `.gitattributes` 설정
- 기본 폴더 구조 생성
- gdx1 접속 복구

완료 조건:

- Mac Studio에서 Unity 프로젝트 열림
- 빈 씬 실행 가능
- Git commit 가능
- gdx1 접속 상태가 문서화됨

### 7.2 1단계: 싱글플레이 조작과 맵

목표:

- 촬영 가능한 작은 폐교 맵에서 플레이어 1명이 움직임

작업:

- 3인칭 또는 1인칭 이동
- 점프/달리기
- 카메라
- 이름표 UI 초안
- 폐교 MVP 맵 블록아웃
- 팀 색상 표시

완료 조건:

- 플레이어가 맵을 돌아다님
- OBS로 화면 녹화 가능
- 플레이어 식별 가능

### 7.3 2단계: 포인트/상점/아이템 1개

목표:

- 게임쇼 핵심 루프 첫 구현

작업:

- 포인트 데이터
- 포인트 UI
- 상점 UI
- 구매 검증
- 첫 아이템: 진실의 펜
- 로그 저장

완료 조건:

- 포인트 획득
- 상점 구매
- 아이템 사용
- 로그 기록

### 7.4 3단계: 아이템 3종 완성

목표:

- 심리전이 생기는 최소 아이템 세트 완성

아이템:

- 진실의 펜
- 위치 스캐너
- 도플갱어 시약

완료 조건:

- 각 아이템의 효과가 UI/게임 상태에 반영
- 운영자가 효과를 관전 가능
- 아이템 사용 로그가 남음

### 7.5 4단계: 2인 멀티플레이

목표:

- 네트워크 구조 검증

작업:

- Host/Client 접속
- 플레이어 스폰
- 위치 동기화
- 이름표 동기화
- 포인트 동기화
- 아이템 사용 동기화

완료 조건:

- 2대 클라이언트가 같은 방에서 플레이
- 포인트/아이템 상태가 서버 기준으로 일치

### 7.6 5단계: 4~8인 테스트

목표:

- 파일럿 촬영 최소 인원 검증

작업:

- 로비
- 팀 배정
- 4~8명 접속
- 간단한 미션
- 타이머
- 생존/탈락 상태

완료 조건:

- 30분 테스트 세션 가능
- 로그로 주요 사건 추적 가능
- 프레임/네트워크 문제 기록

### 7.7 6단계: 운영자 모드

목표:

- 운영자가 판을 진행할 수 있음

작업:

- 운영자 UI
- 포인트 지급/차감
- 아이템 지급
- 팀 변경
- 공지
- 관전 카메라
- 게임 종료

완료 조건:

- 운영자가 Discord 음성 진행과 동시에 게임 상태를 제어 가능

### 7.8 7단계: 방송 UI

목표:

- 유튜브 콘텐츠로 바로 쓸 수 있는 화면 구성

작업:

- 점수판
- 생존자/탈락자 표시
- 남은 시간
- 현재 미션
- 관전 카메라 구도
- OBS용 오버레이 테스트

완료 조건:

- 10분 샘플 녹화본 생성
- 시청자가 상황을 이해할 수 있음

### 7.9 8단계: 첫 파일럿 촬영

목표:

- 실제 사람으로 1회 촬영

작업:

- 참가자 4~8명 모집
- Discord 운영
- OBS 녹화
- 게임 로그 저장
- 문제점 회고

완료 조건:

- 유튜브 본편/쇼츠로 편집 가능한 원본 확보

## 8. 자동화와 검증 계획

`agency-devops-automator` 기준으로 적용할 원칙:

- 수동 실행만 믿지 않음
- 빌드/테스트/로그 수집을 스크립트화
- gdx1은 접속 복구 후 재현 가능한 워커로 사용

### 8.1 로컬 자동화

초기 스크립트 후보:

- `scripts/check_local_env.sh`
- `scripts/build_mac_client.sh`
- `scripts/build_linux_server.sh`
- `scripts/run_local_host_test.sh`
- `scripts/collect_logs.sh`

### 8.2 gdx1 자동화

gdx1 접속 복구 후:

- `scripts/gdx1_sync_build.sh`
- `scripts/gdx1_run_server.sh`
- `scripts/gdx1_run_bots.sh`
- `scripts/gdx1_collect_logs.sh`

gdx1 smoke test:

- Linux headless server 시작
- bot 4개 접속
- 10분 유지
- 포인트 변경 이벤트 발생
- 아이템 사용 이벤트 발생
- 서버 로그 저장
- 종료 코드 확인

## 9. 데이터와 로그

MVP부터 로그를 남긴다.
방송 콘텐츠와 디버깅 모두에 필요함.

필수 로그:

- 게임 시작/종료
- 참가자 접속/이탈
- 팀 배정
- 포인트 변경
- 상점 구매
- 아이템 지급
- 아이템 사용
- 미션 완료
- 탈락/부활
- 운영자 명령

저장 형식:

- 개발 중: JSON Lines
- 파일명: `game_log_YYYYMMDD_HHMMSS.jsonl`
- 저장 위치: `Logs/GameSessions/`

## 10. 현재 가장 큰 리스크

### 10.1 gdx1 일시 단절

현재 gdx1은 Tailscale 목록에는 online으로 보였지만 SSH/핑이 실패했음.
사용자 판단상 곧 복구될 예정이므로, 설계는 GX10 사용 가능 전제로 둔다.

대응:

- Mac Studio 단독 fallback 유지
- gdx1 복구 즉시 Linux server/bot test 워커로 승격
- 모든 gdx1 스크립트는 접속 실패 시 명확한 에러를 내고 중단
- 파일럿 전까지 최소 1회는 gdx1에서 30분 soak test 완료

### 10.2 Unity 미설치

현재 로컬에서 Unity Hub/Editor가 확인되지 않음.

대응:

- Unity 설치를 0단계 최우선 작업으로 둠

### 10.3 Git 저장소 없음

현재 작업 폴더는 Git 저장소가 아님.

대응:

- Unity 프로젝트 생성 전 Git 초기화
- Git LFS 설정
- Unity `.gitignore` 적용

### 10.4 멀티플레이를 너무 빨리 키우는 위험

처음부터 dedicated server, matchmaking, 계정, 클라우드까지 만들면 MVP가 늦어짐.

대응:

- Host/Client로 재미 검증
- 운영자 기능과 방송 가능성을 먼저 확보
- dedicated server는 2인 멀티플레이 성공 뒤 도입

## 11. 바로 다음 실행 순서

### 11.1 오늘 할 일

1. `gdx1` 접속 문제 해결
2. Git 저장소 초기화
3. Git LFS 설치
4. Unity Hub/Unity Editor 설치
5. Unity 프로젝트 생성
6. 기본 폴더 구조 생성
7. 첫 씬 `Boot`, `School_MVP` 생성

### 11.2 gdx1 복구 후 할 일

1. `ssh gdx1 hostname` 성공 확인
2. Ubuntu/ARM/GB10/128GB memory/스토리지 확인
3. NVIDIA driver/container runtime 확인
4. Docker 또는 Podman 사용 가능 여부 확인
5. `~/channel_play` 워커 디렉터리 생성
6. Mac Studio에서 Linux ARM64 server build 생성 가능 여부 확인
7. 불가하면 Linux x86_64/ARM64 빌드 호환성을 Unity 공식 문서 기준으로 재확인
8. gdx1에서 headless server 실행
9. Mac Studio에서 client 접속 테스트
10. gdx1에서 bot 4~8개 접속 테스트
11. 서버 로그와 게임 로그를 Mac Studio로 회수

### 11.3 gdx1 사용 가능 전제의 첫 통합 목표

> Mac Studio에서 Unity Editor로 `School_MVP`를 제작하고, gdx1에서 headless server를 실행하며, Mac Studio 클라이언트 1대가 접속해 이동/포인트/로그가 서버 기준으로 처리되는 것을 확인한다.

이 목표가 완료되면 GX10은 프로젝트의 실제 서버 검증 축으로 편입된다.

### 11.4 첫 번째 개발 목표

첫 개발 목표는 "폐교 맵에서 한 명이 움직이는 것"이 아님.
정확한 첫 목표는 아래임.

> 폐교 MVP 씬에서 플레이어 1명이 움직이고, 운영자 관전 카메라로 그 장면을 볼 수 있으며, OBS로 5분 녹화할 수 있다.

이 목표가 맞아야 이후 포인트/상점/아이템/멀티플레이가 콘텐츠가 됨.

## 12. 완료 기준

1차 MVP 완료 기준:

- 4~8명 접속
- 운영자 1명 접속
- 포인트 지급/차감 가능
- 상점 구매 가능
- 아이템 3개 사용 가능
- 제한시간 작동
- 생존/탈락 상태 표시
- 운영자 관전 가능
- 방송용 UI 표시
- 30분 플레이 가능
- 게임 로그 저장
- OBS 녹화본 생성

## 13. 참고한 외부 기술 기준

- Unity-Technologies Netcode for GameObjects repository
- Unity-Technologies Multiplay examples repository
- ASUS official Ascent GX10 product page
- ASUS official Ascent GX10 tech specs

이 문서의 외부 기술 기준은 2026-06-01 현재 검색 결과 기준이며, Unity 설치 시점에 공식 문서로 한 번 더 확인한다.
