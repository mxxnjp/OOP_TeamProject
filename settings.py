"""게임 전체에서 쓰는 상수(밸런스 수치, 화면 크기, 색상)를 한 곳에 모아둔 파일.
밸런스 조정은 여기 숫자만 바꾸면 된다."""

# ---------------- 화면 ----------------
TILE = 32                      # 타일 한 칸 크기(px)
MAZE_COLS, MAZE_ROWS = 25, 17  # 미로 크기(홀수여야 미로 생성이 깔끔함)
HUD_HEIGHT = 96                # 상단 HUD(체력/인벤토리/전체지도) 높이
SCREEN_W = TILE * MAZE_COLS                # 800
SCREEN_H = HUD_HEIGHT + TILE * MAZE_ROWS   # 640
FPS = 60
TITLE = "HUFS RUN: 졸업 좀 시켜주세요"
FONT_NAMES = "malgungothic,applegothic,nanumgothic"  # 한글 폰트 후보

# ---------------- 구역 ----------------
ZONE_COUNT = 4
# 구역 번호 -> 전체 지도에서의 위치 (열, 행). 중앙(집)은 네 구역 사이에 있음
ZONE_LAYOUT = {1: (0, 0), 2: (1, 0), 3: (0, 1), 4: (1, 1)}
FINAL_ZONE_ID = 5               # 최종 스테이지(구역 4개 키를 다 모으면 열림)
# True면 밤마다 미로 재생성. 단, 재생성하면 바닥 무기가 사라져서 "무기 누적"이 안 됨
MAZE_CHANGES_EACH_NIGHT = False
# 직접 디자인한 맵 파일(assets/ 기준). 없는 건물은 랜덤 미로를 쓴다.
#   맵 기호: # 벽   . 길   H 입구   E 탈출구   P 화분  T 책상  L 조명 (장식은 지나갈 수 없음)
ZONE_MAP_FILES = {1: "maps/library.txt"}
# 과방(중앙) 지도에서 미로 미리보기 대신 보여줄 건물 그림(assets/ 기준). 없는 건물은 미로 미리보기
ZONE_BUILDING_IMAGES = {1: "buildings/library.png"}

# ---------------- 테마(이름) : 여기만 바꾸면 게임 안 글자가 다 바뀜 ----------------
CENTER_NAME = "과방 (교양관)"
ZONE_NAMES = {1: "도서관", 2: "학생회관", 3: "명수당", 4: "기숙사"}
MONSTER_NAMES = {1: "책괴물", 2: "BOO", 3: "물귀신", 4: "경비아저씨"}
# 괴물 그림(assets/ 기준, 배경 투명 PNG). 없으면 사각형으로 그림
MONSTER_SPRITES = {1: "monsters/book.png", 2: "monsters/boo.png",
                   3: "monsters/ghost.png", 4: "monsters/guard.png"}
MONSTER_SPRITE_SIZE = 44   # 괴물 그림이 들어갈 최대 크기(px). 타일(32)보다 조금 크게

# 무기·물약 그림(assets/ 기준). 없으면 도형으로 그림
ITEM_SPRITES = {"spear": "items/spear.png", "bow": "items/bow.png",
                "potion": "items/potion.png", "arrow": "items/arrow.png"}
ITEM_SPRITE_SIZE = 28      # 바닥 아이템 크기(px)
ARROW_SPRITE_SIZE = 24     # 날아가는 화살 크기(px)
SPEAR_SWING_SIZE = 40      # 창 휘두르는 그림 크기(px)
# 그림 속에서 끝(촉)이 가리키는 방향(도, 오른쪽=0, 위=90). 회전시킬 때 기준
SPEAR_SPRITE_ANGLE = 30
ARROW_SPRITE_ANGLE = 180
FINAL_ZONE_NAME = "교수연구동"
BOSS_NAME = "교수님"
KEY_ORDINALS = ("첫번째", "두번째", "세번째", "네번째")

# ---------------- 플레이어 ----------------
PLAYER_MAX_HP = 10
PLAYER_LIVES = 3
PLAYER_MOVE_DELAY = 0.12   # 한 칸 이동 후 다음 이동까지 대기(초)
CENTER_REGEN_PER_SEC = 1   # 중앙에서 초당 회복량
POTION_HEAL_RATIO = 0.5    # 물약: 최대 체력의 50% 회복

# ---------------- 무기 ----------------
SPEAR_DAMAGE = 3
SPEAR_COOLDOWN = 0.45
SPEAR_KNOCKBACK = 1        # 창에 맞으면 몇 칸 밀려나는지
BOW_DAMAGE = 1
BOW_START_ARROWS = 10
BOW_COOLDOWN = 0.3
ARROW_SPEED = 480          # px/초

# ---------------- 괴물 ----------------
MONSTER_MAX_HP = 15
MONSTER_MOVE_DELAY = 0.38
MONSTER_DETECT_RANGE = 12          # 경로 거리 기준 추적 시작 범위
MONSTER_MELEE_DAMAGE = 3
MONSTER_MELEE_COOLDOWN = 1.5       # 근접 공격 간 딜레이(연속 공격 방지)
MONSTER_RANGED_DAMAGE = 2
MONSTER_RANGED_COOLDOWN = 3.0
MONSTER_RANGED_RANGE = 7           # 직선 시야 몇 칸 안이면 독침 발사
DART_SPEED = 260
MONSTER_SPAWN_AWAY_FROM_PLAYER = 8  # 밤이 될 때 플레이어와 최소 몇 칸 떨어져 등장

# ---------------- 최종 보스 (일반 괴물보다 강하게) ----------------
BOSS_MAX_HP = 40
BOSS_MOVE_DELAY = 0.3
BOSS_DETECT_RANGE = 9              # 이보다 멀어지면 탈출구 앞으로 돌아가 지킴
BOSS_MELEE_DAMAGE = 4
BOSS_MELEE_COOLDOWN = 1.2
BOSS_RANGED_DAMAGE = 2
BOSS_RANGED_COOLDOWN = 1.6
BOSS_RANGED_RANGE = 9

# ---------------- 아이템 스폰 (무기 누적) ----------------
DAY_LOOT = {"spear": 1, "bow": 1, "potion": 1}   # 낮이 될 때마다 구역별로 "추가"되는 양
MAX_PICKUPS_PER_ZONE = 12                        # 한 구역에 쌓일 수 있는 최대 아이템 수
FINAL_STAGE_POTIONS = 2                          # 최종 스테이지에 깔려 있는 물약 수

# ---------------- 낮/밤 ----------------
# 낮 제한 시간(초): 1일차 60초, 2일차 40초, 3일차 20초, 4일차부터는 계속 마지막 값(10초)
# 끝나면 그 자리에서 바로 밤
DAY_DURATIONS = (60, 40, 20, 10)
                           # 밤은 시간 제한 없음: 괴물 한 마리를 쓰러뜨리면 다시 낮
TRANSITION_TIME = 2.5      # 안내 화면 표시 시간(아무 키로 스킵)
NIGHT_VISION_RADIUS = 4.5  # 밤 시야(타일 단위)

# ---------------- 색상 ----------------
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GRAY = (130, 130, 130)
BG = (12, 12, 16)
WALL = (52, 78, 52)
WALL_EDGE = (36, 56, 36)
FLOOR = (118, 106, 86)
HUD_BG = (24, 24, 30)
RED = (220, 60, 60)
DARK_RED = (90, 20, 20)
GREEN = (80, 200, 100)
YELLOW = (240, 220, 90)
GOLD = (240, 190, 50)
BLUE = (70, 130, 230)
PURPLE = (160, 70, 210)
MONSTER_COLOR = (120, 40, 40)
BOSS_COLOR = (90, 30, 110)
HOME_COLOR = (90, 150, 200)
DOOR_COLOR = (90, 90, 100)
