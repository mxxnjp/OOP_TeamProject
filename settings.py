"""게임 전체에서 쓰는 상수(밸런스 수치, 화면 크기, 색상)를 한 곳에 모아둔 파일.
밸런스 조정은 여기 숫자만 바꾸면 된다."""

# ---------------- 화면 ----------------
TILE = 32                      # 타일 한 칸 크기(px)
MAZE_COLS, MAZE_ROWS = 25, 17  # 미로 크기(홀수여야 미로 생성이 깔끔함)
HUD_HEIGHT = 96                # 상단 HUD(체력/인벤토리/전체지도) 높이
SCREEN_W = TILE * MAZE_COLS                # 800
SCREEN_H = HUD_HEIGHT + TILE * MAZE_ROWS   # 640
FPS = 60
TITLE = "Maze Escape - OOP Project"
FONT_NAMES = "malgungothic,applegothic,nanumgothic"  # 한글 폰트 후보

# ---------------- 구역 ----------------
ZONE_COUNT = 4
# 구역 번호 -> 전체 지도에서의 위치 (열, 행). 중앙(집)은 네 구역 사이에 있음
ZONE_LAYOUT = {1: (0, 0), 2: (1, 0), 3: (0, 1), 4: (1, 1)}
MAZE_CHANGES_EACH_NIGHT = True  # True: 밤마다 미로 재생성 / False: 고정 미로

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
MONSTERS_PER_ZONE = 1

# ---------------- 낮/밤 ----------------
NIGHT_DURATION = 150       # 밤 지속 시간(초). 끝나면 다시 낮
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
HOME_COLOR = (90, 150, 200)
DOOR_COLOR = (90, 90, 100)
