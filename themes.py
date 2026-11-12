"""미로를 그리는 방식(테마). Zone은 어떤 테마든 theme.render()만 부르면 된다(다형성).

- Theme      : 기본. 벽/바닥을 단색 사각형으로 그림 (그림 파일 없어도 동작)
- ArtTheme   : 그림 한 장(아트)에서 잘라낸 조각으로 벽·바닥·장식을 그림
"""
import os

import pygame

from settings import TILE, WALL, WALL_EDGE, FLOOR

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_image_cache = {}


def load_image(rel_path):
    """assets/ 기준 그림 불러오기 (한 번만 읽고 재사용). 경로가 없거나 파일이 없으면 None."""
    if not rel_path:
        return None
    if rel_path not in _image_cache:
        path = os.path.join(ASSET_DIR, rel_path)
        _image_cache[rel_path] = pygame.image.load(path).convert_alpha() if os.path.exists(path) else None
    return _image_cache[rel_path]


_sprite_cache = {}


def load_sprite(rel_path, box, flash=False):
    """그림을 box x box 안에 비율 유지해서 맞춘 것. flash=True면 맞았을 때용 하얗게 빛나는 버전.
    작은 도트 그림은 각지게(nearest), 큰 그림은 부드럽게(smooth) 줄인다."""
    key = (rel_path, box, flash)
    if key not in _sprite_cache:
        img = load_image(rel_path)
        if img is None:
            _sprite_cache[key] = None
        else:
            w, h = img.get_size()
            k = min(box / w, box / h)
            size = (max(1, round(w * k)), max(1, round(h * k)))
            scale = pygame.transform.scale if max(w, h) < 100 else pygame.transform.smoothscale
            sprite = scale(img, size)
            if flash:
                sprite = sprite.copy()
                sprite.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_ADD)
            _sprite_cache[key] = sprite
    return _sprite_cache[key]


def rotated_sprite(rel_path, box, angle):
    """load_sprite 결과를 angle도(반시계) 돌린 것. 1도 단위로 캐시."""
    angle = int(round(angle)) % 360
    key = ("rot", rel_path, box, angle)
    if key not in _sprite_cache:
        base = load_sprite(rel_path, box)
        _sprite_cache[key] = pygame.transform.rotate(base, angle) if base else None
    return _sprite_cache[key]


class Theme:
    """단색 사각형 테마 (기본값)."""

    def render(self, maze, decor, scale=TILE):
        surf = pygame.Surface((maze.cols * scale, maze.rows * scale))
        surf.fill(FLOOR)
        for y, row in enumerate(maze.grid):
            for x, cell in enumerate(row):
                r = pygame.Rect(x * scale, y * scale, scale, scale)
                if (x, y) in decor:
                    pygame.draw.rect(surf, WALL_EDGE, r.inflate(-scale // 3, -scale // 3), border_radius=3)
                elif cell:
                    pygame.draw.rect(surf, WALL, r)
                    if scale >= 8:
                        pygame.draw.rect(surf, WALL_EDGE, r, 1)
        return surf


class ArtTheme(Theme):
    """아트 이미지에서 (x, y, w, h) 영역을 잘라 타일로 쓰는 테마.

    crops 키:
      floor            바닥
      shelf / shelf2.. 벽 중에서 '아래가 길'인 칸 (정면이 보이는 책장)
      top              벽 중에서 '아래도 벽'인 칸 (책장 윗면)
      border_side      왼쪽/오른쪽 바깥벽
      border_top       맨 위 바깥벽 (창문 등)
      border_bottom    맨 아래 바깥벽
      그 외            장식 (맵 파일의 기호와 연결: decor_symbols)
    """

    def __init__(self, image_file, crops):
        self.image_path = os.path.join(ASSET_DIR, image_file)
        self.crops = crops
        self._sheet = None
        self._tile_cache = {}

    def _tile(self, name, scale):
        key = (name, scale)
        if key not in self._tile_cache:
            if self._sheet is None:
                self._sheet = pygame.image.load(self.image_path).convert_alpha()
            sub = self._sheet.subsurface(self.crops[name])
            self._tile_cache[key] = pygame.transform.smoothscale(sub, (scale, scale))
        return self._tile_cache[key]

    def _wall_tile(self, maze, x, y):
        if y == 0:
            return "border_top"
        if y == maze.rows - 1:
            return "border_bottom"
        if x == 0 or x == maze.cols - 1:
            return "border_side"
        if not maze.is_wall(x, y + 1):              # 아래가 길 -> 책장 정면
            shelves = sorted(k for k in self.crops if k.startswith("shelf"))
            return shelves[(x * 7 + y * 3) % len(shelves)]
        return "top"                                 # 아래도 벽 -> 책장 윗면

    def render(self, maze, decor, scale=TILE):
        if not os.path.exists(self.image_path):     # 그림이 없으면 기본 테마로
            return super().render(maze, decor, scale)
        surf = pygame.Surface((maze.cols * scale, maze.rows * scale))
        for y, row in enumerate(maze.grid):
            for x, cell in enumerate(row):
                pos = (x * scale, y * scale)
                if (x, y) in decor:
                    surf.blit(self._tile("floor", scale), pos)
                    surf.blit(self._tile(decor[(x, y)], scale), pos)
                elif cell:
                    surf.blit(self._tile(self._wall_tile(maze, x, y), scale), pos)
                else:
                    surf.blit(self._tile("floor", scale), pos)
        return surf


# ---------------------------------------------------------------------
# 건물별 테마. 잘라낼 좌표는 원본 아트(1448x1086) 기준 (x, y, 너비, 높이)
# ---------------------------------------------------------------------
LIBRARY_THEME = ArtTheme("tiles/library_art.png", {
    "floor": (1254, 690, 58, 58),
    "shelf": (140, 470, 58, 58),
    "shelf2": (330, 150, 58, 62),
    "shelf3": (880, 940, 58, 62),
    "top": (90, 300, 35, 60),
    "border_side": (0, 400, 40, 60),
    "border_top": (250, 0, 120, 110),
    "border_bottom": (600, 1050, 60, 36),
    "plant": (535, 55, 50, 60),
    "table": (640, 465, 140, 110),
    "lamp": (640, 820, 90, 100),
})

# 맵 파일에서 장식 기호 -> 테마의 그림 이름 (장식은 벽처럼 지나갈 수 없음)
DECOR_SYMBOLS = {"P": "plant", "T": "table", "L": "lamp"}

DEFAULT_THEME = Theme()
ZONE_THEMES = {1: LIBRARY_THEME}   # 구역 번호 -> 테마. 없는 구역은 DEFAULT_THEME
