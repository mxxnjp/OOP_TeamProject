"""맵 구조: Maze(미로 격자) -> Zone(구역 하나) -> World(구역 4개 묶음)."""
import random
from collections import deque

import pygame

from settings import (MAZE_COLS, MAZE_ROWS, TILE, ZONE_COUNT, ZONE_LAYOUT,
                      MAZE_CHANGES_EACH_NIGHT, MONSTERS_PER_ZONE,
                      WALL, WALL_EDGE, FLOOR)
from items import WeaponPickup, PotionPickup, KeyPickup, Spear, Bow, Key
from entities import Monster, DIRECTIONS


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
    """구역(서브 미로) 하나. 미로, 입구(중앙 연결), 탈출구, 아이템, 괴물을 가진다."""

    def __init__(self, zone_id, seed):
        self.id = zone_id
        self.layout_pos = ZONE_LAYOUT[zone_id]
        self.pickups = []
        self.monsters = []
        self.projectiles = []
        self.build_maze(seed)

    def build_maze(self, seed):
        self.rng = random.Random(seed)
        self.maze = Maze(MAZE_COLS, MAZE_ROWS, self.rng)
        lx, ly = self.layout_pos
        # 입구는 중앙(집)을 향한 모서리에 위치
        self.entrance = (MAZE_COLS - 2 if lx == 0 else 1, MAZE_ROWS - 2 if ly == 0 else 1)
        self.dist_from_entrance = self.maze.distances_from(self.entrance)
        # 탈출구는 입구에서 가장 먼 곳
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
    def _random_free_tile(self, min_dist):
        occupied = ({(p.x, p.y) for p in self.pickups} | {(m.x, m.y) for m in self.monsters}
                    | {self.entrance, self.exit_door})
        tiles = [t for t, d in self.dist_from_entrance.items() if d >= min_dist and t not in occupied]
        if not tiles:
            tiles = [t for t in self.dist_from_entrance if t not in occupied]
        return self.rng.choice(tiles)

    def spawn_day_items(self):
        self.pickups = [p for p in self.pickups if isinstance(p, KeyPickup)]
        for make in (lambda x, y: WeaponPickup(x, y, Spear),
                     lambda x, y: WeaponPickup(x, y, Bow),
                     PotionPickup):
            self.pickups.append(make(*self._random_free_tile(min_dist=6)))

    def spawn_night(self, monster_count):
        self.pickups.append(PotionPickup(*self._random_free_tile(min_dist=4)))
        for _ in range(monster_count):
            self.monsters.append(Monster(*self._random_free_tile(min_dist=12), self.rng))

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

        for m in [m for m in self.monsters if not m.alive]:
            self.pickups.append(KeyPickup(m.x, m.y, Key.random(self.rng)))
            game.notify("괴물을 쓰러뜨렸다! 열쇠가 떨어졌다.")
        self.monsters = [m for m in self.monsters if m.alive]

    def collect_pickups(self, player, game):
        for p in list(self.pickups):
            if (p.x, p.y) == (player.x, player.y):
                msg = p.apply(player)
                if msg:
                    self.pickups.remove(p)
                    game.notify(msg)


class World:
    """구역 4개를 관리. 낮/밤 전환 시 스폰과 미로 재생성을 담당."""

    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.generation = 0
        self.zones = {i: Zone(i, self._zone_seed(i)) for i in range(1, ZONE_COUNT + 1)}

    def _zone_seed(self, zone_id):
        return self.seed * 1000 + self.generation * 10 + zone_id

    def start_day(self):
        for z in self.zones.values():
            z.clear_monsters()
            z.spawn_day_items()

    def start_night(self):
        if MAZE_CHANGES_EACH_NIGHT:
            self.generation += 1
            for z in self.zones.values():
                z.build_maze(self._zone_seed(z.id))
        for z in self.zones.values():
            z.spawn_night(MONSTERS_PER_ZONE)
