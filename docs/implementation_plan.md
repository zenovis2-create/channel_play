# channel_play Implementation Plan

작성일: 2026-06-01
프로젝트 이름: `channel_play`
기준 문서: `master_plan.md`, `real_plan.md`

## 0. 현재 판정

`channel_play`는 Unity 기반 구독자 참여형 3D 게임쇼 MVP다.
첫 구현 목표는 "큰 게임"이 아니라 "촬영 가능한 작은 폐교 게임쇼 세트장"이다.

현재 검증 상태:

- Mac Studio M2 Ultra 64GB: 로컬 제작 본진으로 사용 가능
- 작업 경로: `/Volumes/AI2/channel_play`
- Git 저장소: 초기화됨
- Git LFS: 설치 및 local hook 설정 완료
- Unity Hub: 설치 완료
- Unity Editor: `6000.0.76f1` arm64 설치 완료
- Unity 라이선스: 미활성화, 프로젝트 생성 차단 중
- gdx1: Tailscale online, SSH 인증 실패
- gdx1 표준 호스트명: `gdx1`

## 1. 구현 원칙

1. Unity Editor는 Mac Studio에서 실행한다.
2. gdx1은 Linux headless server, bot test, soak test, 로그 수집 워커로 쓴다.
3. gdx1이 끊기면 Mac Studio Host/Client fallback으로 진행한다.
4. 포인트, 상점, 아이템, 미션, 타이머는 서버 권한으로 설계한다.
5. 운영자 기능과 OBS 녹화 가능성을 그래픽 품질보다 먼저 완성한다.
6. 파일럿 전까지 30분 세션과 로그 저장을 반드시 검증한다.

## 2. 절차 순서

### Phase 0: Repository Foundation

목표: Unity 프로젝트 생성 전 저장소와 작업 규칙 고정.

작업:

1. Git 저장소 초기화
2. Unity용 `.gitignore` 추가
3. Unity용 `.gitattributes` / Git LFS 패턴 추가
4. `docs/implementation_plan.md` 작성
5. `scripts/check_local_env.sh` 작성
6. `scripts/probe_gdx1.sh` 작성

완료 조건:

- `git status`가 문서/설정/스크립트를 추적 대상으로 보여줌
- `.maru`, `.DS_Store`, Unity `Library/`, `Temp/`, `Builds/`가 Git에서 제외됨
- 로컬 환경 점검 스크립트가 실행됨

### Phase 1: Local Toolchain

목표: Mac Studio에서 Unity 제작 가능 상태 확보.

작업:

1. Unity Hub 설치
2. Unity LTS 설치
3. Git LFS 설치
4. OBS 설치
5. Blender 설치
6. IDE 설정
7. `scripts/check_local_env.sh` 재실행

완료 조건:

- Unity 프로젝트 생성 가능
- Git LFS 사용 가능
- OBS로 화면 녹화 가능

### Phase 2: Unity Project Bootstrap

목표: `channel_play` Unity 프로젝트 생성.

작업:

1. Unity URP 프로젝트 생성
2. 프로젝트명을 `channel_play`로 설정
3. `_Project` 폴더 구조 생성
4. `Boot`, `School_MVP`, `OperatorView`, `OverlayTest` 씬 생성
5. Netcode for GameObjects 후보 패키지 확인
6. 첫 empty scene 실행

완료 조건:

- Unity Editor에서 프로젝트 열림
- 빈 씬 Play 가능
- 첫 Unity 메타 파일들이 Git에 잡힘

### Phase 3: First Playable Camera Loop

목표: 폐교 MVP 씬에서 플레이어 1명이 움직이고 운영자 관전 카메라로 촬영 가능.

작업:

1. 플레이어 이동
2. 카메라
3. 이름표
4. 팀 색상
5. 폐교 맵 블록아웃
6. 운영자 관전 카메라 초안
7. OBS 5분 녹화 테스트

완료 조건:

- 플레이어가 맵을 이동
- 관전 카메라로 보기 가능
- OBS 녹화본 생성

### Phase 4: Game Show Core Loop

목표: 포인트, 상점, 아이템 1개, 로그 저장.

작업:

1. `PlayerData`
2. `PointSystem`
3. `ShopSystem`
4. `ItemSystem`
5. `GameLogSystem`
6. 첫 아이템 `진실의 펜`

완료 조건:

- 포인트 획득/차감
- 상점 구매
- 아이템 사용
- JSON Lines 로그 저장

### Phase 5: Multiplayer Slice

목표: 2인 Host/Client 후 gdx1 headless server로 확장.

작업:

1. Netcode bootstrap
2. Player spawn
3. 위치/이름표 동기화
4. 포인트 동기화
5. 아이템 사용 동기화
6. Linux headless server build
7. gdx1 server 실행
8. Mac Studio client 접속

완료 조건:

- 2인 접속 성공
- 서버 기준 상태 일치
- gdx1 server 로그 회수

### Phase 6: Operator Mode

목표: 운영자가 판을 진행할 수 있음.

작업:

1. 운영자 UI
2. 참가자 목록
3. 위치 보기
4. 포인트 지급/차감
5. 아이템 지급
6. 팀 변경
7. 공지
8. 타이머 시작/정지
9. 관전 카메라 이동

완료 조건:

- 운영자가 Discord 진행과 동시에 게임 상태 제어 가능

### Phase 7: 4-8 Player Session

목표: 파일럿 직전 세션 검증.

작업:

1. 로비
2. 팀 배정
3. 간단한 미션
4. 아이템 3종
5. 생존/탈락 상태
6. 4-8 bot 또는 실제 클라이언트 접속
7. 30분 soak test

완료 조건:

- 30분 세션 유지
- 주요 사건 로그 추적 가능
- OBS 화면에서 상황 이해 가능

### Phase 8: Pilot Recording

목표: 유튜브 본편/쇼츠로 쓸 수 있는 첫 원본 확보.

작업:

1. 참가자 4-8명 모집
2. Discord 세팅
3. OBS 녹화
4. 운영자 진행
5. 게임 로그 저장
6. 회고 문서 작성

완료 조건:

- 편집 가능한 원본 영상
- 게임 로그
- 다음 버전 수정 목록

## 3. 지금 당장 처리할 작업

1. Unity Hub에서 로그인 및 라이선스 활성화
2. `./scripts/create_unity_project.sh` 재실행
3. gdx1 SSH 인증 문제 정리
4. Unity 프로젝트 생성 확인
5. `_Project` 폴더 구조 생성
6. 첫 씬 `Boot`, `School_MVP`, `OperatorView` 생성

## 4. gdx1 현재 이슈

gdx1은 Tailscale에는 online으로 보인다.
하지만 SSH 인증이 실패한다.

확인된 실패:

- `ssh daehan@gdx1`: Permission denied
- `ssh zenovis1@gdx1`: Permission denied
- `ssh root@gdx1`: Permission denied

다음 조치:

- gdx1에 Mac Studio 공개키 등록
- 또는 Tailscale SSH 활성화
- 또는 임시 비밀번호 로그인 허용 후 키 등록

## 5. 첫 통합 목표

> Mac Studio에서 Unity Editor로 `School_MVP`를 제작하고, gdx1에서 headless server를 실행하며, Mac Studio 클라이언트 1대가 접속해 이동/포인트/로그가 서버 기준으로 처리되는 것을 확인한다.

이 목표가 끝나면 `channel_play`는 실제 구현 단계로 진입한다.
