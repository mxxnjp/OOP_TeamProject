"""맵 구조: Maze(미로 격자) -> Zone(건물 하나) / FinalZone(최종 스테이지) -> World(전체)."""
import os
import random
from collections import deque

from settings import (MAZE_COLS, MAZE_ROWS, TILE, ZONE_COUNT, ZONE_LAYOUT, FINAL_ZONE_ID,
                      MAZE_CHANGES_EACH_NIGHT, MONSTER_SPAWN_AWAY_FROM_PLAYER, ZONE_MAP_FILES,
                      ZONE_NAMES, MONSTER_NAMES, MONSTER_SPRITES, FINAL_ZONE_NAME, BOSS_NAME,
                      DAY_LOOT, MAX_PICKUPS_PER_ZONE, FINAL_STAGE_POTIONS,
                      COURTYARD_ZONES, BUILDING_BAND_ROWS, COURTYARD_WALL_DENSITY,
                      COURTYARD_COLS, COURTYARD_ROWS, COURTYARD_STEP, COURTYARD_LOOPS, DECOR_PER_ZONE)
from items import WeaponPickup, PotionPickup, Spear, Bow
from entities import Monster, Boss, DIRECTIONS
from themes import ASSET_DIR, DECOR_SYMBOLS, DEFAULT_THEME, ZONE_THEMES

LOOT_FACTORIES = {
    "spear": lambda x, y: WeaponPickup(x, y, Spear),
    "bow": lambda x, y: WeaponPickup(x, y, Bow),
    "potion": PotionPickup,
}


class Maze:
    """0 = 길, 1 = 벽. 랜덤 생성(generate) 또는 맵 파일(from_file)로 만든다."""

    def __init__(self, grid):
        self.grid = grid
        self.rows, self.cols = len(grid), len(grid[0])

    @classmethod
    def generate(cls, cols, rows, rng):
        """재귀 백트래킹으로 생성 후 고리(loop)를 조금 뚫어 전투 공간 확보."""
        maze = cls([[1] * cols for _ in range(rows)])
        maze._carve(rng)
        maze._add_loops(rng, ratio=0.08)
        return maze

    @classmethod
    def from_file(cls, path):
        """텍스트 맵 파일 읽기. (미로, {'H': 입구, 'E': 탈출구}, {좌표: 장식이름}) 반환."""
        with open(path, encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f if line.strip()]
        grid, markers, decor = [], {}, {}
        for y, line in enumerate(lines):
            row = []
            for x, ch in enumerate(line):
                if ch in DECOR_SYMBOLS:
                    decor[(x, y)] = DECOR_SYMBOLS[ch]
                    row.append(1)
                elif ch == "#":
                    row.append(1)
                else:
                    row.append(0)
                    if ch in "HE":
                        markers[ch] = (x, y)
            grid.append(row)
        if not grid or any(len(r) != len(grid[0]) for r in grid):
            raise ValueError(f"{path}: 맵의 모든 줄은 길이가 같아야 합니다.")
        return cls(grid), markers, decor

    def _carve(self, rng):
        self.grid[1][1] = 0
        stack = [(1, 1)]
        while stack:
            x, y = stack[-1]
            neighbors = [(x + dx * 2, y + dy * 2, dx, dy) for dx, dy in DIRECTIONS
                         if 0 < x + dx * 2 < self.cols - 1 and 0 < y + dy * 2 < self.rows - 1
                         and self.grid[y + dy * 2][x + dx * 2] == 1]
            if neighbors:
                nx, ny, dx, dy = rng.choice(neighbors)
                self.grid[y + dy][x + dx] = 0
                self.grid[ny][nx] = 0
                stack.append((nx, ny))
            else:
                stack.pop()

    def _add_loops(self, rng, ratio):
        for y in range(1, self.rows - 1):
            for x in range(1, self.cols - 1):
                if self.grid[y][x] == 1 and rng.random() < ratio:
                    horizontal = self.grid[y][x - 1] == 0 and self.grid[y][x + 1] == 0
                    vertical = self.grid[y - 1][x] == 0 and self.grid[y + 1][x] == 0
                    if horizontal != vertical:
                        self.grid[y][x] = 0

    def is_wall(self, x, y):
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return True
        return self.grid[y][x] == 1

    def _bfs(self, start):
        parents = {start: None}
        dist = {start: 0}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for dx, dy in DIRECTIONS:
                nxt = (x + dx, y + dy)
                if nxt not in dist and not self.is_wall(*nxt):
                    dist[nxt] = dist[(x, y)] + 1
                    parents[nxt] = (x, y)
                    queue.append(nxt)
        return dist, parents

    def distances_from(self, start):
        return self._bfs(start)[0]

    def next_step(self, start, goal):
        """start에서 goal로 가는 최단경로의 다음 칸과 경로 길이. 길이 없으면 (None, inf)."""
        dist, parents = self._bfs(goal)   # goal에서 거꾸로 탐색하면 parent가 곧 다음 칸
        if start not in dist:
            return None, float("inf")
        return parents[start], dist[start]

    @classmethod
    def courtyard(cls, cols, rows, rng, band_rows, density, step=3, tries=4, loops=0):
        """'건물 앞마당' 미로. 위쪽 band_rows 줄은 건물 그림 자리(벽으로 막음),
        그 아래는 담장으로 둘러싼 마당에 ㄱ·ㄴ·T자 벽 조각을 랜덤으로 세운다.

        - 벽은 step칸 간격 격자점(기둥) 사이에만 세운다. step=2면 통로 1칸(복잡), 3이면 2칸(널찍).
        - 길이 끊기지 않게 하는 방법 (Union-Find): 벽들이 고리(닫힌 원)를 만들면 그 안이 갇힌다.
          그래서 "이미 벽으로 이어진 두 기둥 사이"에는 벽을 세우지 않는다. 담장 전체는 한 덩어리로 친다.
          → 길 찾기 없이도 모든 길이 항상 이어져 있다 (그래서 큰 미로도 빠르게 만들어짐).
        - 여러 번 만들어 보고 입구 → 탈출구 경로가 가장 긴 것을 고른다.
        - 위 방법만 쓰면 길이 '나무 모양'이라 어디서 어디로 가든 길이 딱 하나뿐(갈림길은 전부 막다른 길).
          그래서 마지막에 벽 loops칸을 뚫어 돌아가는 길(고리)을 만든다 → 길이 여러 갈래가 됨.
        반환: (미로, {"H": 입구, "E": 탈출구})
        """
        top, bottom = band_rows + 1, rows - 2               # 마당 안쪽 첫 줄 / 마지막 줄
        entrance, exit_ = (cols // 2, bottom), (cols // 2, top)
        keep = {(entrance[0] + d, entrance[1]) for d in (-1, 0, 1)} | \
               {(exit_[0] + d, exit_[1]) for d in (-1, 0, 1)}
        xs = list(range(step, cols - 1, step))              # 격자점 x
        ys = list(range(top + step - 1, bottom, step))      # 격자점 y

        BORDER = "border"                                   # 담장 전체 = 기둥 하나로 취급

        def segments():
            """(칸 목록, 한쪽 기둥, 다른쪽 기둥) 목록. 담장에 붙는 조각은 한쪽이 BORDER."""
            segs = []
            for y in ys:
                row = [0] + xs + [cols - 1]
                for a, b in zip(row, row[1:]):
                    na = BORDER if a == 0 else (a, y)
                    nb = BORDER if b == cols - 1 else (b, y)
                    segs.append(([(x, y) for x in range(a, b + 1) if 0 < x < cols - 1], na, nb))
            for x in xs:
                col = [band_rows] + ys + [rows - 1]
                for a, b in zip(col, col[1:]):
                    na = BORDER if a == band_rows else (x, a)
                    nb = BORDER if b == rows - 1 else (x, b)
                    segs.append(([(x, y) for y in range(a, b + 1) if top <= y <= bottom], na, nb))
            return segs

        best, best_len = None, -1
        for _ in range(tries):
            grid = [[1] * cols for _ in range(rows)]
            for y in range(top, bottom + 1):
                for x in range(1, cols - 1):
                    grid[y][x] = 0
            parent = {}

            def find(node):                                 # Union-Find: 같은 벽 덩어리인지
                parent.setdefault(node, node)
                while parent[node] != node:
                    parent[node] = parent[parent[node]]
                    node = parent[node]
                return node

            inner = (bottom - top + 1) * (cols - 2)
            walls = 0
            segs = segments()
            rng.shuffle(segs)
            for cells, na, nb in segs:
                if walls >= inner * density:
                    break
                if any(c in keep for c in cells):
                    continue
                ra, rb = find(na), find(nb)
                if ra == rb:                                # 이미 이어진 벽끼리 -> 고리가 생겨서 갇힘
                    continue
                parent[ra] = rb
                for x, y in cells:
                    if grid[y][x] == 0:
                        grid[y][x] = 1
                        walls += 1
            maze = cls(grid)
            maze.open_loops(rng, loops, top, bottom, keep)  # 고리를 뚫은 뒤에 길이를 재야 실제 난이도
            length = maze.distances_from(entrance).get(exit_, -1)
            if length > best_len:
                best, best_len = maze, length
        return best, {"H": entrance, "E": exit_}

    def open_loops(self, rng, count, top, bottom, keep=()):
        """벽 count칸을 뚫어 길에 고리(돌아가는 길)를 만든다. 길을 막지는 않으므로 연결은 그대로 유지.
        뚫을 수 있는 칸: 양옆(또는 위아래)이 길이고 반대쪽 두 칸은 벽인 '얇은 벽'. 큰 빈 공간이 생기지 않게.
        막다른 길 옆의 벽을 먼저 뚫어서 막다른 길이 줄어들게 하고, 뚫은 곳끼리는 3칸 이상 떨어뜨린다."""
        g, cols = self.grid, self.cols

        def floor(x, y):
            return 0 <= x < cols and 0 <= y < self.rows and g[y][x] == 0

        def degree(x, y):
            return sum(floor(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))

        candidates = []
        for y in range(top, bottom + 1):
            for x in range(1, cols - 1):
                if g[y][x] == 0 or (x, y) in keep:
                    continue
                horizontal = floor(x - 1, y) and floor(x + 1, y) and not floor(x, y - 1) and not floor(x, y + 1)
                vertical = floor(x, y - 1) and floor(x, y + 1) and not floor(x - 1, y) and not floor(x + 1, y)
                if horizontal or vertical:
                    sides = [(x - 1, y), (x + 1, y)] if horizontal else [(x, y - 1), (x, y + 1)]
                    near_dead_end = any(degree(*c) == 1 for c in sides)
                    candidates.append((not near_dead_end, rng.random(), x, y))
        candidates.sort()                                       # 막다른 길 옆부터, 그다음은 랜덤
        opened = []
        for _, _, x, y in candidates:
            if len(opened) >= count:
                break
            if all(abs(x - ox) + abs(y - oy) >= 3 for ox, oy in opened):
                g[y][x] = 0
                opened.append((x, y))
        return opened


class Zone:
    """건물(서브 미로) 하나. 미로, 입구(중앙 연결), 탈출구, 아이템, 괴물을 가진다.
    탈출구는 처음엔 숨겨져 있고, 마지막(4번째) 키를 이 구역에서 얻으면 나타난다."""
    is_final = False

    def __init__(self, zone_id, seed):
        self.id = zone_id
        self.name = ZONE_NAMES.get(zone_id, f"{zone_id}구역")
        self.monster_name = MONSTER_NAMES.get(zone_id, "괴물")
        self.pickups = []
        self.monsters = []
        self.projectiles = []
        self.exit_open = False
        self.build_maze(seed)

    def pick_entrance(self):
        """입구는 중앙(과방)을 향한 모서리."""
        lx, ly = ZONE_LAYOUT[self.id]
        cols, rows = self.maze.cols, self.maze.rows
        return (cols - 2 if lx == 0 else 1, rows - 2 if ly == 0 else 1)

    def build_maze(self, seed):
        self.rng = random.Random(seed)
        self.theme = ZONE_THEMES.get(self.id, DEFAULT_THEME)
        map_file = ZONE_MAP_FILES.get(self.id)
        if self.id in COURTYARD_ZONES:   # 건물 + 앞마당 랜덤 미로
            self.maze, markers = Maze.courtyard(COURTYARD_COLS, COURTYARD_ROWS, self.rng,
                                                BUILDING_BAND_ROWS, COURTYARD_WALL_DENSITY,
                                                step=COURTYARD_STEP, loops=COURTYARD_LOOPS)
            self.decor = self.place_decor(markers)
        elif map_file:    # 직접 디자인한 맵
            self.maze, markers, self.decor = Maze.from_file(os.path.join(ASSET_DIR, map_file))
        else:             # 랜덤 미로
            self.maze, markers, self.decor = Maze.generate(MAZE_COLS, MAZE_ROWS, self.rng), {}, {}
        self.entrance = markers.get("H") or self.pick_entrance()
        self.dist_from_entrance = self.maze.distances_from(self.entrance)
        # 탈출구 자리: 맵에 E가 있으면 거기, 없으면 입구에서 가장 먼 곳
        self.exit_door = markers.get("E") or max(self.dist_from_entrance, key=self.dist_from_entrance.get)
        self.pickups.clear()
        self.monsters.clear()
        self.projectiles.clear()
        self._surface_cache = {}

    def place_decor(self, markers):
        """테마에 장식 그림이 있으면 막다른 길 칸에 놓는다. 장식 칸은 벽처럼 못 지나간다.
        막다른 길(이웃 길이 1칸뿐)은 막아도 다른 길이 끊기지 않아서 안전하다."""
        names = self.theme.decor_names
        if not names:
            return {}
        maze = self.maze
        avoid = set()
        for x, y in markers.values():                     # 입구·탈출구 근처는 비워 둠
            avoid |= {(x + dx, y + dy) for dx in range(-2, 3) for dy in range(-2, 3)}

        def floor_neighbors(x, y):
            return sum(not maze.is_wall(x + dx, y + dy) for dx, dy in DIRECTIONS)

        dead_ends = [(x, y) for y in range(maze.rows) for x in range(maze.cols)
                     if not maze.is_wall(x, y) and (x, y) not in avoid and floor_neighbors(x, y) == 1]
        self.rng.shuffle(dead_ends)
        decor = {}
        for x, y in dead_ends[:DECOR_PER_ZONE]:
            if floor_neighbors(x, y) == 1:                # 앞에서 놓은 장식 때문에 바뀌었을 수 있음
                maze.grid[y][x] = 1
                decor[(x, y)] = self.rng.choice(names)
        return decor

    def surface(self, scale=TILE):
        if scale not in self._surface_cache:
            self._surface_cache[scale] = self.theme.render(self.maze, self.decor, scale)
        return self._surface_cache[scale]

    # ---------- 스폰 ----------
    def _random_free_tile(self, min_dist, avoid=None, avoid_dist=0):
        occupied = ({(p.x, p.y) for p in self.pickups} | {(m.x, m.y) for m in self.monsters}
                    | {self.entrance, self.exit_door})

        def ok(tile, need_dist):
            if tile in occupied or self.dist_from_entrance[tile] < need_dist:
                return False
            return avoid is None or abs(tile[0] - avoid[0]) + abs(tile[1] - avoid[1]) >= avoid_dist

        tiles = [t for t in self.dist_from_entrance if ok(t, min_dist)]
        if not tiles:
            tiles = [t for t in self.dist_from_entrance if ok(t, 0)] or \
                    [t for t in self.dist_from_entrance if t not in occupied]
        return self.rng.choice(tiles)

    def spawn_day_items(self):
        """낮마다 아이템을 '추가'한다(안 주운 것은 그대로 남아 누적). 최대 개수 제한 있음.
        아이템은 낮이 시작될 때만 생기고, 밤에는 새로 생기지 않는다."""
        for kind, count in DAY_LOOT.items():
            for _ in range(count):
                if len(self.pickups) >= MAX_PICKUPS_PER_ZONE:
                    return
                self.pickups.append(LOOT_FACTORIES[kind](*self._random_free_tile(min_dist=6)))

    def spawn_night_monster(self, avoid=None):
        tile = self._random_free_tile(min_dist=12, avoid=avoid, avoid_dist=MONSTER_SPAWN_AWAY_FROM_PLAYER)
        self.monsters.append(Monster(*tile, self.rng, self.monster_name, MONSTER_SPRITES.get(self.id)))

    def clear_monsters(self):
        self.monsters.clear()
        self.projectiles = [p for p in self.projectiles if p.from_player]

    # ---------- 조회 ----------
    def monster_at(self, x, y):
        for m in self.monsters:
            if (m.x, m.y) == (x, y):
                return m
        return None

    # ---------- 매 프레임 ----------
    def update(self, dt, player, game):
        for m in self.monsters:
            m.update(dt, self, player)
        for p in self.projectiles:
            p.update(dt, self, player)
        self.projectiles = [p for p in self.projectiles if p.alive]

        dead = [m for m in self.monsters if not m.alive]
        self.monsters = [m for m in self.monsters if m.alive]
        for m in dead:
            game.on_monster_killed(self, m)

    def items_available(self, game):
        """아이템을 보고 주울 수 있는 때: 낮, 또는 최종 스테이지(보스전용 물약)."""
        return not game.is_night or self.is_final

    def collect_pickups(self, player, game):
        if not self.items_available(game):      # 밤에는 아이템을 주울 수 없음 (다음 낮까지 그대로 남음)
            return
        for p in list(self.pickups):
            if (p.x, p.y) == (player.x, player.y):
                msg = p.apply(player)
                if msg:
                    self.pickups.remove(p)
                    game.notify(msg)


class FinalZone(Zone):
    """최종 스테이지(교수연구동). 보스가 최종 탈출구 바로 앞을 막고 있다.
    보스를 쓰러뜨리면 탈출구가 열린다. 입장할 때마다 보스전이 처음부터 시작."""
    is_final = True

    def __init__(self, seed):
        super().__init__(FINAL_ZONE_ID, seed)
        self.name = FINAL_ZONE_NAME
        self.monster_name = BOSS_NAME

    def pick_entrance(self):
        return (1, self.maze.rows - 2)

    def build_maze(self, seed):
        super().build_maze(seed)
        # 보스 자리: 탈출구에서 입구 방향으로 한 칸 앞 (= 탈출구를 막는 위치)
        self.boss_home = self.maze.next_step(self.exit_door, self.entrance)[0]

    def reset_encounter(self):
        self.clear_monsters()
        self.projectiles.clear()
        self.exit_open = False
        self.monsters.append(Boss(*self.boss_home, self.rng, BOSS_NAME))
        while sum(isinstance(p, PotionPickup) for p in self.pickups) < FINAL_STAGE_POTIONS:
            self.pickups.append(PotionPickup(*self._random_free_tile(min_dist=4)))


class World:
    """건물 4개 + 최종 스테이지를 관리. 낮/밤 전환 시 스폰을 담당."""

    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.generation = 0
        self.zones = {i: Zone(i, self._zone_seed(i)) for i in range(1, ZONE_COUNT + 1)}
        self.final = FinalZone(self._zone_seed(FINAL_ZONE_ID))

    def _zone_seed(self, zone_id):
        return self.seed * 1000 + self.generation * 10 + zone_id

    def clear_monsters(self):
        for z in self.zones.values():
            z.clear_monsters()

    def start_day(self):
        self.clear_monsters()
        for z in self.zones.values():
            z.spawn_day_items()

    def start_night(self, cleared_zone_ids, player_zone=None, player_pos=None):
        """아직 키를 얻지 못한 건물에만 괴물 1마리씩 등장.
        플레이어가 구역 안에 있으면 그 근처에는 나오지 않게 한다."""
        if MAZE_CHANGES_EACH_NIGHT:
            self.generation += 1
            for z in self.zones.values():
                z.build_maze(self._zone_seed(z.id))
        for z in self.zones.values():
            if z.id not in cleared_zone_ids:
                z.spawn_night_monster(avoid=player_pos if z is player_zone else None)
