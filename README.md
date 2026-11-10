# Maze Escape (pygame OOP 프로젝트 기본 틀)

```bash
python main.py
```

## 게임 흐름
1. 시작: 미로 한가운데(중앙/집)에 떨어짐 → 전체 지도 화면
2. **낮**: 구역(1~4)을 **우클릭**해서 입장 → 미로 탐험하면서 창/활/물약 줍기 (지나가면 자동 습득)
3. 구역 입구(`H` 칸)로 돌아오면 중앙으로 복귀. 중앙은 안전지대이고 체력이 회복됨
4. 중앙에서 **N** → 안내 화면 → **밤** (미로 재생성, 각 구역에 괴물 등장, 시야 제한)
5. 괴물을 무기로만 처치 가능 → 죽으면 **열쇠**(구역 번호 + 코드)를 떨어뜨림
6. 열쇠에 적힌 구역의 `EXIT` 칸으로 가면 탈출 성공 (다른 구역의 탈출구는 안 열림)
7. 밤이 끝나면(150초) 다시 낮 → 새 무기/물약 생성
8. 사망 시 목숨 -1 후 중앙에서 부활, 목숨 3개 다 잃으면 GAME OVER → R로 전체 리셋

## 조작
| 키 | 동작 |
|---|---|
| WASD / 방향키 | 이동 |
| 우클릭 | 공격 (마우스 방향) / 중앙 화면에서는 구역 입장 |
| 1, 2 | 창 / 활 선택 |
| 스페이스 | 무기 순환 변경 |
| 3 | 물약 (최대 체력 50% 회복) |
| N | (중앙, 낮) 밤 시작 |
| ESC | 일시정지 |

## 파일 구조 (클래스)
| 파일 | 클래스 | 역할 |
|---|---|---|
| `settings.py` | – | 밸런스 수치·색상·화면 크기 상수 (여기만 고치면 밸런스 조정) |
| `game.py` | `Game` | 메인 루프, 낮/밤 타이머, 화면 전환, 사망/승리 처리 |
| `scenes.py` | `Scene` → `CenterScene`, `ZoneScene`, `TransitionScene`, `EndScene` | 화면별 입력·업데이트·그리기 |
| `world.py` | `Maze`, `Zone`, `World` | 미로 생성(백트래킹)·BFS 길찾기, 구역별 아이템/괴물 관리 |
| `entities.py` | `Entity` → `Player`, `Monster` | 체력·이동·공격, 괴물 AI(추적/배회/근접/독침) |
| `items.py` | `Weapon` → `Spear`, `Bow` / `Pickup` → `WeaponPickup`, `PotionPickup`, `KeyPickup` / `Key`, `Inventory` | 무기·아이템·인벤토리 |
| `projectiles.py` | `Projectile` → `Arrow`, `PoisonDart` | 화살·독침 |
| `hud.py` | – | 상단 HUD(목숨, 체력 10칸, 슬롯, 열쇠, 전체 지도) |

### OOP 포인트
- **상속**: `Entity` → `Player`/`Monster`, `Weapon` → `Spear`/`Bow`, `Pickup` → 3종, `Scene` → 4종
- **다형성**: `weapon.attack()`, `pickup.apply()`, `scene.update()/draw()`를 같은 이름으로 호출해도 클래스마다 다르게 동작
- **추상 클래스**: `Weapon`, `Pickup`은 `ABC` + `@abstractmethod`
- **캡슐화**: 인벤토리 조작은 `Inventory` 메서드로만 (`add_weapon`, `cycle`, `select_slot`)

## 기획서 대비 구현 수치
- 플레이어 체력 10, 목숨 3 / 괴물 체력 15
- 창 3 데미지 + 1칸 넉백, 활 1 데미지(화살 10개, 활을 또 주우면 +10)
- 괴물 근접 3 (1.5초 쿨타임), 독침 2 (직선 시야 7칸 이내, 3초 쿨타임)
- 미로 고정/변경: `settings.MAZE_CHANGES_EACH_NIGHT`

## 앞으로 붙일 것 (TODO 아이디어)
- 이미지 스프라이트로 교체 (`draw()` 메서드만 바꾸면 됨)
- 밤 전환 안내 영상 (`TransitionScene` 자리)
- 탈출구에서 열쇠 코드 입력 UI
- 효과음 / 배경음

## 컨셉변경
- 추후 논의했던 학교컨셉(ex. 미로가 대학원, 학생회관, 도서관)으로 변경.