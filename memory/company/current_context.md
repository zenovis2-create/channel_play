# Current Context

Project: `channel_play`

Date: 2026-06-01

Current production direction:

- Unity game is the product.
- Channel Play Studio is the production cockpit.
- Channel Play Agent Company is the team/orchestration layer.
- Mac Studio is the Unity/Blender/OBS implementation machine.
- gdx1 is reserved for server, bot, soak-test, and background worker jobs after SSH authentication is fixed.

Integrated goal:

- ID: `mvp_traitor_escape_gameshow`
- Goal: 8명이 접속하고 운영자가 포인트/아이템을 주며 OBS로 촬영 가능한 작은 3D 게임쇼 세트장을 만든다.
- First game mode: `배신자 탈출게임`
- Success criterion: 게임 출시가 아니라 파일럿 영상 1편을 만들 수 있는 플레이 가능한 세션.
- First development milestone: Unity에서 플레이어가 작은 3D 맵을 돌아다니고, 화면에 포인트가 표시되는 상태.

MVP scope:

- 참가자 4~8명 접속
- 작은 3D 맵 1개
- 운영자 1명 접속
- 제한시간 30~40분
- 팀 구분
- 포인트 획득
- 상점 이용
- 아이템 3개 사용: 진실의 펜, 위치 스캐너, 도플갱어 시약
- 운영자 관전 모드
- 기본 점수판/상태창
- OBS 녹화 가능

First mode rules:

- 일반 참가자는 제한시간 안에 열쇠 3개를 찾아 최종 탈출문을 연다.
- 배신자는 정체를 숨기고 일반 참가자의 탈출을 방해한다.
- 모든 참가자는 미션으로 포인트를 얻고 상점 아이템을 구매한다.

Current constraints:

- One writer per Unity scene, prefab folder, or script system.
- Agent work must produce evidence before completion.
- Shared memory must be updated after meaningful decisions.
- Do not ask an agent to build the whole game at once. Split work into scoped, verifiable tasks.
