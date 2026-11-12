# HUFS RUN: 졸업 좀 시켜주세요 (pygame OOP 프로젝트)

```bash
python main.py
```

## 게임 흐름
1. **시작**: 중앙 **과방(교양관)** 에서 시작 → 전체 지도 화면 (안전지대, 체력 회복)
2. **낮 (1일차 60초 → 2일차 40초 → 3일차 20초 → 4일차부터 10초)**: 건물(도서관 / 학생회관 / 명수당 / 기숙사)을 클릭해서 입장 → 무기·물약 파밍 (지나가면 자동 습득)
   - 건물 입구(`H` 칸)로 가면 과방으로 복귀. 여러 건물을 돌아다닐 수 있음
   - 안 주운 아이템은 사라지지 않고 **다음 날까지 누적**됨 (미로는 고정)
3. **밤 (시간 제한 없음)**: 낮 시간이 끝나면 **그 자리에서 바로** 밤 → 아직 키를 못 얻은 건물에 괴물 등장
   - 아무 건물에서나 괴물 1마리를 쓰러뜨리면 그 건물의 **키** 획득 → "첫번째 키를 획득하였습니다" → 다시 낮
4. 반복해서 건물 4곳의 키를 모두 모으면 → "모든 구역 키를 획득하였습니다"
   - 마지막 괴물을 쓰러뜨린 건물에 **탈출구(EXIT)** 가 나타남 (낮으로 바뀌지 않음)
5. **최종 스테이지 (교수연구동)**: 최종 보스가 최종 탈출구 앞을 막고 있음 → 쓰러뜨리면 탈출구가 열림
   - 보스전에서 죽으면 키는 유지한 채 과방으로 → 다시 낮부터 무기 파밍 → 마지막 키를 얻은 건물의 EXIT(계속 열려 있음)로 가서 재도전
   - 교수연구동은 과방 지도에 없고, EXIT로만 갈 수 있음
6. **엔딩**: 졸업! → **대학원 vs 취업** 선택 → 시즌2 암시
7. 사망 시 목숨 -1, 목숨 3개 다 잃으면 GAME OVER → 처음부터

## 조작
| 키 | 동작 |
|---|---|
| WASD / 방향키 | 이동 |
| 좌클릭 | 공격 (마우스 방향) / 과방 지도에서는 건물 입장 |
| J | 공격 (바라보는 방향, 마우스 없이 플레이) |
| 1, 2 | 창 / 활 선택 |
| 3 | 물약 (최대 체력 50% 회복) |
| ESC | 일시정지 |
| F11 | 전체화면 / 창 모드 전환 |

## 파일 구조 (클래스)
| 파일 | 클래스 | 역할 |
|---|---|---|
| `settings.py` | – | 밸런스 수치·건물/괴물 이름·색상 상수 (여기만 고치면 밸런스·테마 조정) |
| `game.py` | `Game` | 메인 루프, 낮 타이머, 낮/밤 전환, 키 획득, 화면 전환, 사망/엔딩 처리 |
| `scenes.py` | `Scene` → `CenterScene`, `ZoneScene`, `TransitionScene`, `MenuScene`(→ `PauseScene`, `GraduationScene`), `EndScene` | 화면별 입력·업데이트·그리기 |
| `world.py` | `Maze`, `Zone` → `FinalZone`, `World` | 미로 생성(백트래킹)/맵 파일 읽기·BFS 길찾기, 건물별 아이템/괴물, 최종 스테이지 |
| `themes.py` | `Theme` → `ArtTheme` | 미로 그리기 (단색 / 아트 이미지에서 잘라낸 타일) |
| `entities.py` | `Entity` → `Player`, `Monster` → `Boss` | 체력·이동·공격, 괴물 AI(추적/배회/근접/독침), 보스(탈출구 지키기) |
| `items.py` | `Weapon` → `Spear`, `Bow` / `Pickup` → `WeaponPickup`, `PotionPickup` / `Key`, `Inventory` | 무기·아이템·키·인벤토리 |
| `projectiles.py` | `Projectile` → `Arrow`, `PoisonDart` | 화살·독침 |
| `hud.py` | – | 상단 HUD(목숨, 체력 10칸, 슬롯, 키 4칸, 낮 타이머, 전체 지도) |

### OOP 포인트
- **상속**: `Entity` → `Player`/`Monster` → `Boss`, `Zone` → `FinalZone`, `Weapon` → `Spear`/`Bow`, `Pickup` → 2종, `Scene` → `MenuScene` → `PauseScene`/`GraduationScene`
- **오버라이드**: `Boss`는 능력치(클래스 속성)와 `choose_step()`만 바꿔서 "탈출구를 지키는 강한 괴물"이 됨. `FinalZone`은 `pick_entrance()`/`build_maze()`만 바꿈
- **다형성**: `weapon.attack()`, `pickup.apply()`, `monster.choose_step()`, `scene.update()/draw()`를 같은 이름으로 호출해도 클래스마다 다르게 동작
- **추상 클래스**: `Weapon`, `Pickup`은 `ABC` + `@abstractmethod`
- **캡슐화**: 인벤토리 조작은 `Inventory` 메서드로만 (`add_weapon`, `add_key`, `has_key_for`, `select_slot`)

## 건물 맵 직접 디자인하기
- 맵 파일: `assets/maps/건물.txt` (가로 25 x 세로 17 글자), 등록: `settings.ZONE_MAP_FILES`
- 기호: `#` 벽, `.` 길, `H` 입구(과방 쪽 모서리), `E` 탈출구, `P` 화분, `T` 책상, `L` 조명 (장식은 못 지나감)
- 규칙: 바깥 테두리는 전부 벽 / 모든 길이 이어져 있어야 함
- 그림(테마): `themes.py`에서 아트 이미지의 어느 부분을 바닥·책장·장식으로 쓸지 좌표로 지정 → `ZONE_THEMES`에 등록
- 맵 파일이 없는 건물은 랜덤 미로 + 단색 그림
- 현재: 1. 도서관 = `maps/library.txt` + `tiles/library_art.png`
- 과방 지도의 건물 그림: `assets/buildings/건물.png` (배경 투명 PNG) → `settings.ZONE_BUILDING_IMAGES`에 등록. 없으면 미로 미리보기
  - 현재: 1. 도서관 = `buildings/library.png`

## 현재 수치 (`settings.py`)
- 플레이어 체력 10, 목숨 3 / 괴물 체력 15 / **보스 체력 40**
- 창 3 데미지 + 1칸 넉백, 활 1 데미지(화살 10개, 활을 또 주우면 +10)
- 괴물 근접 3 (1.5초 쿨타임), 독침 2 (직선 7칸, 3초 쿨타임)
- 보스 근접 4 (1.2초), 독침 2 (직선 9칸, 1.6초), 9칸보다 멀어지면 탈출구 앞으로 복귀
- 낮 60 / 40 / 20 / 10초 (`DAY_DURATIONS`, 4일차부터 10초 고정) / 밤 무제한, 낮마다 건물별 창1·활1·물약1 추가 (건물당 최대 12개 누적)

## 앞으로 붙일 것 (TODO)
- 밸런스 조정 (특히 최종 보스 난이도, 무기 파밍 양)
- 배경·플레이어·괴물 디자인 (`draw()` 메서드와 `Maze.render()`만 바꾸면 됨)
- 최종 보스·플레이어 그림 (괴물 그림은 `settings.MONSTER_SPRITES`, 크기는 `MONSTER_SPRITE_SIZE`)
- (완료) 무기·물약·화살 그림: `assets/items/`, 설정은 `settings.ITEM_SPRITES` (바닥 아이템, 날아가는 화살, 창 찌르기, HUD 칸)
- 게임 시작 / 엔딩 스토리 화면
- 효과음 / 배경음
- (보류) 전투 시 주인공 시점 카메라

## 테마
| 장소 | 괴물 |
|---|---|
| 중앙: 과방(교양관) | – (안전지대) |
| 1. 도서관 | 책괴물 (`monsters/book.png`) |
| 2. 학생회관 | BOO (`monsters/boo.png`) |
| 3. 명수당 | 물귀신 (`monsters/ghost.png`) |
| 4. 기숙사 | 경비아저씨 (`monsters/guard.png`) |
| 최종: 교수연구동 | 최종 보스 (`settings.BOSS_NAME`) |
