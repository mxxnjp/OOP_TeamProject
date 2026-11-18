"""게임 전체에서 쓰는 상수(밸런스 수치, 화면 크기, 색상)를 한 곳에 모아둔 파일.
밸런스 조정은 여기 숫자만 바꾸면 된다."""

# ---------------- 화면 ----------------
TILE = 32                      # 타일 한 칸 크기(px)
VIEW_COLS, VIEW_ROWS = 25, 17  # 화면에 한 번에 보이는 칸 수
MAZE_COLS, MAZE_ROWS = 25, 17  # 기본 랜덤 미로·맵 파일 크기 (최종 스테이지 등. 홀수여야 깔끔함)
HUD_HEIGHT = 96                # 상단 HUD(체력/인벤토리/전체지도) 높이
SCREEN_W = TILE * VIEW_COLS                # 800
SCREEN_H = HUD_HEIGHT + TILE * VIEW_ROWS   # 640
# 미로가 화면보다 크면 카메라가 플레이어를 따라 움직인다
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
# "건물 + 앞마당" 랜덤 미로를 쓰는 구역 (새 게임마다 미로가 바뀜)
#   위쪽 BUILDING_BAND_ROWS 줄에는 그 건물 그림, 아래는 담장 두른 마당 + ㄱ·ㄴ·T자 벽 조각
COURTYARD_ZONES = (1, 2, 3, 4)
COURTYARD_COLS = 25              # 앞마당 미로 가로 칸 수 (홀수). 화면(25칸)과 같으면 스크롤 없이 한 화면
COURTYARD_ROWS = 17              # 세로 칸 수 (COURTYARD_ROWS - BUILDING_BAND_ROWS 가 홀수여야 함)
BUILDING_BAND_ROWS = 4           # 건물 그림이 차지하는 줄 수 (4줄 = 128px)
COURTYARD_STEP = 2               # 벽 격자 간격. 2 = 통로 1칸(복잡), 3 = 통로 2칸(널찍)
COURTYARD_WALL_DENSITY = 0.5     # 마당 안쪽에서 벽이 차지하는 최대 비율 (클수록 복잡)
COURTYARD_LOOPS = 7              # 벽을 몇 칸 뚫어 돌아가는 길을 만들지 (0 = 길이 딱 하나뿐인 미로, 클수록 갈래가 많음)
DECOR_PER_ZONE = 14              # 타일 세트에 장식이 있는 건물: 막다른 길에 놓을 장식 수 (못 지나감)
# 직접 디자인한 맵 파일(assets/ 기준). COURTYARD_ZONES에서 빼면 이 맵을 쓴다. 둘 다 없으면 기본 랜덤 미로.
#   맵 기호: # 벽   . 길   H 입구   E 탈출구   P 화분  T 책상  L 조명 (장식은 지나갈 수 없음)
ZONE_MAP_FILES = {}              # 예: {2: "maps/dormitory.txt"} (지금은 모든 건물이 랜덤 앞마당 미로)
# 과방(중앙) 지도에서 미로 미리보기 대신 보여줄 건물 그림(assets/ 기준). 없는 건물은 미로 미리보기
ZONE_BUILDING_IMAGES = {1: "buildings/library.png", 2: "buildings/student_hall.png",
                        3: "buildings/myeongsudang.png", 4: "buildings/dormitory.png"}
# 과방 지도 디자인 그림(assets/ui/center_design.png)에서 각 건물을 잘라 올 영역 (x, y, w, h, 원본 그림 기준).
#   건물은 그림 속 위치 그대로 화면에 놓임. 디자인 그림이 없으면 위 ZONE_BUILDING_IMAGES를 씀
CENTER_MAP_CROPS = {1: (120, 262, 640, 205),    # 도서관 (왼쪽 위)
                    2: (915, 257, 640, 208),    # 학생회관 (오른쪽 위)
                    3: (85, 640, 620, 268),     # 명수당 (왼쪽 아래)
                    4: (1000, 632, 630, 266)}   # 기숙사 (오른쪽 아래)
# 과방 지도 색감: 메인 디자인 그림(center_design.png)의 색 분포(채널별 평균, 표준편차)에 그림들을 맞춤
#   배경(밤하늘·숲)은 아래 값으로, 건물·과방은 디자인 그림 속 같은 건물 부분(CENTER_MAP_CROPS)에서 자동으로 잼
CENTER_TONE_BG = ((48, 50, 65), (24, 20, 22))
CENTER_ROOM_IMAGE = "buildings/center_room.png"    # 지도 가운데 과방 그림
CENTER_LABEL = "AI데이터융합학부 과방"             # 과방 그림 위 이름표
MAIN_BACKGROUND = "ui/main_background.png"   # 과방 지도 화면 전체 + HUD 뒤에 깔리는 배경 그림
CENTER_IMAGE = "buildings/center_door.png"   # 지도 가운데 과방 그림 (없으면 파란 원)

# ---------------- 테마(이름) : 여기만 바꾸면 게임 안 글자가 다 바뀜 ----------------
CENTER_NAME = "과방 (교양관)"
ZONE_NAMES = {1: "도서관", 2: "학생회관", 3: "명수당", 4: "기숙사"}
MONSTER_NAMES = {1: "책귀", 2: "BOO", 3: "물귀신", 4: "경비아저씨"}
# 괴물 그림(assets/ 기준, 배경 투명 PNG). 없으면 사각형으로 그림
#   방향별 그림(앞/뒤/옆): {"down": 앞모습, "up": 뒷모습, "left": 왼쪽, "right": 오른쪽}. 그림 한 장(문자열)도 가능
def _four_ways(name, folder="monsters"):
    return {d: f"{folder}/{name}_{d}.png" for d in ("down", "up", "left", "right")}


MONSTER_SPRITES = {1: _four_ways("book"), 2: _four_ways("boo"),
                   3: _four_ways("ghost"), 4: _four_ways("guard")}
MONSTER_SPRITE_SIZE = 44   # 괴물 그림이 들어갈 최대 크기(px). 타일(32)보다 조금 크게

# 플레이어 캐릭터 (시작할 때 선택). 그림: assets/player/boy_down.png 처럼 방향별 4장
PLAYER_CHARACTERS = {
    "boy": {"name": "남학생", "sprites": _four_ways("boy", "player"), "color": (70, 130, 230)},
    "girl": {"name": "여학생", "sprites": _four_ways("girl", "player"), "color": (230, 120, 170)},
}
PLAYER_SPRITE_SIZE = 44

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
