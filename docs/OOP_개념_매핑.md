# 수업 개념 ↔ HUFS RUN 코드 매핑

OOP 수업 자료(1·4·5·6·7·8·9강)에 나온 개념이 우리 코드 어디에 들어 있는지 정리한 표.
위치는 `파일:줄` (2026-11-16 기준 코드). 코드를 고치면 줄 번호는 조금씩 밀릴 수 있음.

---

## 1강. 객체지향이란 (4대 특징)

| 개념 | 우리 코드 | 설명 |
|---|---|---|
| 추상화 | `themes.py:60` `Theme`, `scenes.py:22` `Scene`, `items.py:19` `Weapon` | "그린다(render)", "화면(handle_event/update/draw)", "공격한다(attack)"처럼 공통 틀만 정하고 세부는 자식이 채움 |
| 캡슐화 | `items.py:144` `Inventory` | 무기·물약·키를 한 객체에 묶고, 바깥에서는 `add_weapon`, `add_key`, `has_key_for`, `select_slot` 메서드로만 다룸 |
| 상속 | `entities.py` `Entity → Player / Monster → Boss` 등 (아래 5강 참고) | 공통 기능은 부모에, 다른 점만 자식에 |
| 다형성 | `game.py:175-181` `self.scene.handle_event / update / draw` | 지금 화면이 무엇이든 같은 이름으로 호출 → 화면마다 다르게 동작 |
| 객체끼리 메시지 | `world.py:206` `game.on_monster_killed(...)`, `projectiles.py:40` `target.take_damage(...)` | 독립된 객체들이 메서드 호출로 서로 소통 |
| 모듈화 → 업무분담 | 파일 9개 (화면/맵/캐릭터/아이템/그리기/설정) | 팀원별로 파일 단위로 나눠 작업 가능 |

## 4강. 클래스 객체

| 개념 | 우리 코드 | 설명 |
|---|---|---|
| 클래스 = 설계도, 인스턴스화 | `world.py` `Monster(*tile, ...)`로 밤마다 괴물 객체 생성 | 같은 `Monster` 설계도로 건물마다 다른 괴물(이름·그림) 생성 |
| 인스턴스 변수 | `entities.py` `self.x, self.y, self.hp`, `items.py` `self.arrows` | 객체마다 따로 갖는 값, 생성자에서 초기화 |
| 클래스 변수 | `entities.py:122~` `Monster.max_hp, move_delay ...`, `scenes.py:23-24` `Scene.advances_clock, pausable`, `items.py:52-54` `Spear.name, damage` | 같은 클래스 객체가 공유하는 값. 자식 클래스에서 값만 덮어써서 성격을 바꿈 |
| 생성자 `__init__` | 모든 클래스 | 예: `Player.__init__` 에서 목숨·인벤토리 초기화 |
| 인스턴스 메서드 | 대부분의 메서드 | `self`로 자기 데이터 사용 |
| 클래스 메서드 `@classmethod` | `world.py:28-37` `Maze.generate()`, `Maze.from_file()` | 인스턴스 없이 클래스로 호출해 미로 객체를 "만드는" 메서드 |
| 정적 메서드 `@staticmethod` | `scenes.py:185` `ZoneScene.to_world()` | `self`가 필요 없는 좌표 변환 유틸리티 |
| 메서드를 값으로 (Bound method in dict/list) | `scenes.py:335,356` 메뉴 `options = [("계속하기", self.resume), ...]` → `self.options[i][1]()` / `world.py:14` `LOOT_FACTORIES` 딕셔너리 | 강의 p31 "Method as Value in Dictionary → This is OOP!" 그대로 |
| 상속·오버라이딩 | 아래 5강 | |

## 5강. 상속과 다형성

| 개념 | 우리 코드 | 설명 |
|---|---|---|
| 상속 계층 | `Entity → Player`, `Entity → Monster → Boss` / `Weapon → Spear, Bow` / `Pickup → WeaponPickup, PotionPickup` / `Projectile → Arrow, PoisonDart` / `Zone → FinalZone` / `Theme → CourtyardTheme, TileTheme, ImageTheme` / `Scene → CenterScene, ZoneScene, TransitionScene, EndScene, MenuScene → PauseScene, GraduationScene` | 클래스 31개, 상속 관계 20개 이상 |
| `super()` 재사용 | `entities.py:65,134,239`, `items.py:58,108`, `projectiles.py:49,66` 등 20곳 | 부모의 초기화를 그대로 쓰고 자식 속성만 추가 |
| 생성자 오버라이딩 = 재사용 + 후처리 | `world.py:230-231` `FinalZone.build_maze()` → `super().build_maze(seed)` 후 보스 자리 계산 | 강의 p13 "재사용 + 후처리 = 확장" 그대로 |
| 세부단계 오버라이딩 (공통 실행 메서드 + 훅) | `entities.py:142,167` `Monster.update()`가 `self.choose_step()` 호출 → `Boss`는 `choose_step()`만 오버라이드(`entities.py:242`) / `items.py` `Pickup.draw()`가 `draw_shape()` 호출 | 전체 흐름은 부모가, 바뀌는 단계만 자식이 |
| 메서드 오버라이딩 | `Spear.update`, `Bow.merge/label`, `Arrow.draw`, `TileTheme.render` 등 | |
| 추상 클래스 ABC | `items.py:19` `Weapon(ABC)` + `@abstractmethod attack` (`items.py:40`), `items.py:196` `Pickup(ABC)` + `@abstractmethod apply` (`items.py:203`) | 직접 객체화 막고, 자식에게 구현 강제 (강의 실습 2번과 같은 구조) |
| 상속을 이용한 다형성 | `p.attack()` → 창은 칸 찌르기(`items.py:65`), 활은 화살 발사(`items.py:115`) / `pickup.apply()` / `theme.render()` | 같은 메서드, 객체 타입에 따라 다른 동작 |
| 생성자 오버로딩 효과 (classmethod) | `Maze.generate()` vs `Maze.from_file()` | 강의 p23 "Class method로 생성자 오버로딩 효과" — 랜덤 미로 / 맵 파일 두 가지 방식으로 Maze 생성 |
| 덕 타이핑 | `scenes.py:257-263` 아이템·괴물·투사체·플레이어를 모두 `.draw(surf)`로 그림 | `Pickup`, `Monster`, `Projectile`, `Player`는 공통 부모가 없는데도(일부) 같은 이름 메서드만 있으면 동작 |
| `@property` | `entities.py:31` `alive`, `items.py:29` `ready`, `items.py:153,164` `current_weapon`, `key_count`, `projectiles.py:24` `tile`, `game.py:59` `all_keys_collected` | 메서드를 속성처럼 `( )` 없이 사용 |
| 연산자 오버로딩 (간접) | `items.py:136` `@dataclass(frozen=True) class Key` → `items.py:162` `Key(zone_id) in self.keys` | dataclass가 `__eq__`, `__hash__`를 자동으로 만들어 줘서 키 비교·집합 사용 가능 |

## 6강. 캡슐화와 추상화

| 개념 | 우리 코드 | 설명 |
|---|---|---|
| 캡슐 = 그룹 + 보호 + 은닉 | `Inventory`, `Player.drink_potion()` (`entities.py:98`) | 물약 개수 확인·최대 체력 확인 같은 규칙을 메서드 안에 숨김 |
| 데이터 검증 | `entities.py:35-41` `take_damage()`는 체력이 0 밑으로, `heal()`은 최대치 위로 못 가게 | 강의 "음수 나이는 없다"와 같은 검증. (단, setter가 아니라 메서드로 구현) |
| 계산된 값은 getter로 | `@property key_count`, `alive`, `tile` | 값을 저장하지 않고 필요할 때 계산 |
| 추상화 = 인터페이스만 드러내기 | `Theme.render(maze, decor, scale)` 하나만 알면 단색/아트/그림 테마를 다 씀 | 내부 구현(타일 자르기, 이미지 스케일)은 숨김 |
| ABC + `@abstractmethod` | `Weapon`, `Pickup` | "인스턴스로 쓰지 않는 틀" |

## 7강. 고급 프로그래밍

| 개념 | 우리 코드 | 설명 |
|---|---|---|
| 절차형 vs 객체지향 | 전체 구조 | 상태(체력, 위치, 인벤토리)와 책임(이동, 공격)을 객체로 묶음 |
| if-elif 분기 대신 다형성 | 무기 종류마다 `if weapon == "spear": ... elif ...` 대신 `weapon.attack()` | 새 무기는 `Weapon`을 상속한 클래스 하나만 추가하면 됨 |
| 리팩토링 – 모듈화 | 미로 그리기를 `Maze`에서 `themes.py`로 분리 | 기능은 그대로, 구조만 개선 |
| 리팩토링 – 중복 제거 | `PauseScene`의 메뉴 코드를 `MenuScene`으로 올리고 `GraduationScene`과 공유 | Deduplication |
| 리팩토링 – 죽은 코드 제거 | 기획 변경 후 `KeyPickup`, 무기 순환 `cycle()`, 열쇠 코드 삭제 | Dead code elimination |
| 리팩토링 – 이름 바꾸기 | 괴물·건물 이름을 `settings.py` 한 곳에서만 관리 | Renaming이 쉬운 구조 |
| 멀티스레드 | **없음** | (아래 "빠진 것" 참고) |

## 8강. PyGame 기초

| 개념 | 우리 코드 | 설명 |
|---|---|---|
| 창 만들기 | `game.py:24` `pygame.display.set_mode(...)` | |
| 이벤트 기반 무한 루프 | `game.py:183-187` `run()`: `clock.tick` → `event.get()` → `display.flip()` | 강의의 기본 템플릿 구조 |
| QUIT 처리 | `game.py` `step()` | |
| 이미지 로딩 / blit | `themes.py` `load_image()` (`pygame.image.load`), 곳곳의 `surf.blit(...)` | |
| `get_rect(기준점=)` | `entities.py:209` `midbottom`, `hud.py:22` `center/topleft`, `scenes.py:69` `center` | 강의 p25 topleft/center/midbottom 기준점 |
| 마우스 클릭 | `scenes.py:82,198` `MOUSEBUTTONDOWN`, `event.button` (1=좌, 3=우), `event.pos` | |
| `Rect.collidepoint` | `scenes.py:84` 건물 클릭, `scenes.py:359,363` 메뉴 버튼 | |
| 키보드 `K_` 상수 | `K_1~K_3`, `K_j`, `K_ESCAPE`, `K_F11`, `K_RETURN` | |
| `get_pressed()` (누르고 있는 키) | `scenes.py:212` 이동 | 강의 p31 그대로 — 꾹 누르면 계속 이동 |
| `colliderect` | **없음** | 우리는 칸(타일) 좌표 비교로 충돌 판정 |

## 9강. PyGame + OOP

| 개념 | 우리 코드 | 설명 |
|---|---|---|
| 도형 그리기 `draw.line/circle/rect/polygon` | `hud.py:15-17` 하트(원 2개 + 다각형), `entities.py:59-60` 체력바, `items.py` 그림 없을 때 도형 | |
| "모든 객체는 init / update / draw" (Ball 클래스) | `Player`, `Monster`, `Projectile`, `Zone`, 모든 `Scene` | 강의 Ball Bouncer v2와 같은 패턴 |
| 버튼 클래스 `SimpleButton` (normal / hover / active, `handleEvent`, `draw`) | `buttons.py` `SimpleButton` — 강의 p24-28 구조 그대로 (상태 3개, `collidepoint`로 판단, 눌렀다 뗄 때 클릭 + `callBack`). `ZoomButton(SimpleButton)`은 hover 그림을 1.2배로 자동 생성 → `CenterScene`에서 건물 그림에 마우스를 올리면 커짐 | 강의는 그림 3장(buttonUp/Down/Hover)을 받지만, 상속으로 한 장에서 만들어 냄 |
| 한글 텍스트 출력 | `game.py:26-29` `SysFont("malgungothic"...)`, `hud.py:21` `font.render` → blit | 강의 p31 malgungothic 그대로 |
| 콜백 함수 | `scenes.py:290-301` `TransitionScene(on_finish=...)`, `scenes.py:330-350` `MenuScene(on_cancel=...)`, `scenes.py:412-413` 졸업 메뉴 `lambda` | "타이밍은 화면이, 무엇을 할지는 바깥에서" — 강의 p36 그대로 |

---

## 수업에 나왔지만 아직 코드에 없는 것 (넣으면 좋은 순서)

| 개념 | 강의 | 넣을 만한 곳 (제안) |
|---|---|---|
| private 속성 `__변수` | 4강, 6강 | `Entity`의 체력을 `self.__hp`로 숨기기 |
| `@property` + `@x.setter` (검증) | 6강 | 위 `__hp`에 getter/setter를 달아서 0 ~ 최대 체력으로 자동 제한 → 지금 `take_damage`, `heal`에 흩어진 검증을 한 곳으로 |
| 연산자 오버로딩 / `__str__` | 5강 | `Key`나 `Entity`에 `__str__` (예: `print(key)` → "도서관 키"), 좌표 클래스에 `__add__` |
| `colliderect` | 8강 | 화살·독침이 맞았는지를 `Rect.colliderect`로 판정 |
| 다중 상속 / MRO | 5강 | 억지로 넣을 필요는 없음. 넣는다면 `Boss(Monster, 원거리공격Mixin)` 정도 |
| 멀티스레드 | 7강 | 게임 루프에는 필요 없음. 넣는다면 시작 화면에서 그림 파일 미리 읽기 정도 (pygame 화면 작업은 메인 스레드에서만 해야 해서 주의) |
