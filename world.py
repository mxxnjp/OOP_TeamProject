"""맵 구조: Maze(미로 격자) -> Zone(건물 하나) / FinalZone(최종 스테이지) -> World(전체)."""
import random
from collections import deque

import pygame

from settings import (MAZE_COLS, MAZE_ROWS, TILE, ZONE_COUNT, ZONE_LAYOUT, FINAL_ZONE_ID,
                      MAZE_CHANGES_EACH_NIGHT, MONSTER_SPAWN_AWAY_FROM_PLAYER,
                      ZONE_NAMES, MONSTER_NAMES, FINAL_ZONE_NAME, BOSS_NAME,
                      DAY_LOOT, MAX_PICKUPS_PER_ZONE, FINAL_STAGE_POTIONS,
                      WALL, WALL_EDGE, FLOOR)
from items import WeaponPickup, PotionPickup, Spear, Bow
from entities import Monster, Boss, DIRECTIONS

LOOT_FACTORIES = {
    "spear": lambda x, y: WeaponPickup(x, y, Spear),
    "bow": lambda x, y: WeaponPickup(x, y, Bow),
    "potion": PotionPickup,
}


class Maze:
    """0 = 길, 1 = 벽. 재귀 백트래킹으로 생성 후 고리(loop)를 조금 뚫어 전투 공간 확보."""

    def __init__(self, cols, rows, rng):
        self.cols, self.rows = cols, rows
        self.grid = [[1] * cols for _ in range(rows)]
        self._carve(rng)
        self._add_loops(rng, ratio=0.08)

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

    def render(self, scale=TILE):
        surf = pygame.Surface((self.cols * scale, self.rows * scale))
        surf.fill(FLOOR)
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell:
                    r = pygame.Rect(x * scale, y * scale, scale, scale)
                    pygame.draw.rect(surf, WALL, r)
                    if scale >= 8:
                        pygame.draw.rect(surf, WALL_EDGE, r, 1)
        return surf


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
        return (MAZE_COLS - 2 if lx == 0 else 1, MAZE_ROWS - 2 if ly == 0 else 1)

    def build_maze(self, seed):
        self.rng = random.Random(seed)
        self.maze = Maze(MAZE_COLS, MAZE_ROWS, self.rng)
        self.entrance = self.pick_entrance()
        self.dist_from_entrance = self.maze.distances_from(self.entrance)
        # 탈출구 자리는 입구에서 가장 먼 곳
        self.exit_door = max(self.dist_from_entrance, key=self.dist_from_entrance.get)
        self.pickups.clear()
        self.monsters.clear()
        self.projectiles.clear()
        self._surface_cache = {}

    def surface(self, scale=TILE):
        if scale not in self._surface_cache:
            self._surface_cache[scale] = self.maze.render(scale)
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
        """낮마다 아이템을 '추가'한다(안 주운 것은 그대로 남아 누적). 최대 개수 제한 있음."""
        for kind, count in DAY_LOOT.items():
            for _ in range(count):
                if len(self.pickups) >= MAX_PICKUPS_PER_ZONE:
                    return
                self.pickups.append(LOOT_FACTORIES[kind](*self._random_free_tile(min_dist=6)))

    def spawn_night_monster(self, avoid=None):
        tile = self._random_free_tile(min_dist=12, avoid=avoid, avoid_dist=MONSTER_SPAWN_AWAY_FROM_PLAYER)
        self.monsters.append(Monster(*tile, self.rng, self.monster_name))

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

    def collect_pickups(self, player, game):
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
        return (1, MAZE_ROWS - 2)

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
