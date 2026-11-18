"""미로를 그리는 방식(테마). Zone은 어떤 테마든 theme.render()만 부르면 된다(다형성).

- Theme      : 기본. 벽/바닥을 단색 사각형으로 그림 (그림 파일 없어도 동작)
- TileTheme  : 벽·바닥 타일 그림 여러 장을 칸마다 섞어 깔아 그림 (랜덤 미로용)
- ImageTheme : 미로 그림 한 장을 통째로 배경으로 씀 (벽/길 판정은 맵 파일)
"""
import json
import os
import sys

import pygame

from settings import TILE, WALL, WALL_EDGE, FLOOR, BUILDING_BAND_ROWS

# 그림 폴더 위치. .exe(PyInstaller)로 실행하면 함께 묶인 파일이 임시 폴더(sys._MEIPASS)에 풀리므로 거기서 찾음
_BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(_BASE_DIR, "assets")
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
    decor_names = []        # 이 테마가 가진 장식 그림 이름들 (있으면 Zone이 미로에 배치)

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


class TileTheme(Theme):
    """벽·바닥 타일 그림 여러 장으로 미로를 그리는 테마. 랜덤 미로에도 그대로 쓸 수 있다.

    folder          타일 폴더 (assets/ 기준)
    floors          바닥 타일 파일 이름들 (칸마다 섞어 씀)
    walls           벽 타일 (가로로 이어진 벽, 또는 방향 구분 없는 벽)
    walls_vertical  세로로 이어진 벽 전용 타일 (없으면 walls를 씀)
    """

    def __init__(self, folder, floors, walls, walls_vertical=None):
        self.folder = folder
        self.floors = floors
        self.walls = walls
        self.walls_vertical = walls_vertical or walls

    @staticmethod
    def _variant(names, x, y):
        """칸 좌표로 변형을 고름. 같은 칸은 늘 같은 그림 (매 프레임 바뀌지 않게)."""
        return names[(x * 7 + y * 13 + (x * y) % 5) % len(names)]

    def _tile(self, name, scale):
        img = load_image(f"{self.folder}/{name}")
        return pygame.transform.smoothscale(img, (scale, scale)) if img else None

    @staticmethod
    def _is_vertical(maze, x, y):
        """위아래로만 벽이 이어지면 세로 벽. 미로 밖은 벽으로 치지 않는다."""
        def solid(cx, cy):
            return 0 <= cx < maze.cols and 0 <= cy < maze.rows and maze.grid[cy][cx] == 1
        up_down = solid(x, y - 1) or solid(x, y + 1)
        left_right = solid(x - 1, y) or solid(x + 1, y)
        return up_down and not left_right

    def render(self, maze, decor, scale=TILE):
        if load_image(f"{self.folder}/{self.floors[0]}") is None:   # 그림이 없으면 기본 테마로
            return super().render(maze, decor, scale)
        cache = {}

        def tile(name):
            if name not in cache:
                cache[name] = self._tile(name, scale)
            return cache[name]

        surf = pygame.Surface((maze.cols * scale, maze.rows * scale))
        for y, row in enumerate(maze.grid):
            for x, cell in enumerate(row):
                if cell:
                    names = self.walls_vertical if self._is_vertical(maze, x, y) else self.walls
                else:
                    names = self.floors
                surf.blit(tile(self._variant(names, x, y)), (x * scale, y * scale))
        return surf


class CourtyardTheme(Theme):
    """참고 그림 한 장에서 잘라낸 조각으로 '건물 + 앞마당 미로'를 그리는 테마.

    sheet      조각을 잘라낼 그림 (assets/ 기준)
    band       위쪽 띠에 그릴 건물 영역 (x, y, w, h)
    floors     바닥 조각들 [(x, y, w, h), ...]  칸마다 섞어 씀
    wall       벽 윗면 + 앞면 조각 (위가 비어 있는 벽 칸)
    wall_body  벽 몸통 조각 (바로 위도 벽인 칸: 세로로 이어지는 벽)
    band_rows  건물 띠가 차지하는 줄 수
    """
    BAND_BG = (21, 26, 31)
    LAMP_GLOW = (255, 196, 110)

    def __init__(self, sheet, band, floors, wall, wall_body, band_rows):
        self.sheet = sheet
        self.band = band
        self.floors = floors
        self.wall = wall
        self.wall_body = wall_body
        self.band_rows = band_rows

    def _crop(self, rect, w, h):
        return pygame.transform.smoothscale(load_image(self.sheet).subsurface(rect), (w, h))

    BORDER_DARK = 90        # 참고 그림 조각 테두리(검은 틀) 판정: 한 줄 평균 밝기(R+G+B)가 이보다 어두우면 틀
    EDGE_SAMPLE = 0.04           # 양옆 빈 곳 색을 가져올 그림 가장자리 폭 (그림 폭 대비)
    EDGE_FADE = 40               # 건물 그림과 양옆 배경을 부드럽게 섞는 폭(px, 화면 기준)
    COVER_IF_GAP = 0.15          # 양옆 빈 곳이 띠 폭의 이 비율보다 작으면 채우지 않고 그림을 키워 꽉 채움

    def _trimmed_band(self):
        """band 영역에서 바깥 검은 틀(테두리)을 잘라낸 영역. 한 번 계산해 둠."""
        if not hasattr(self, "_band_trim"):
            import numpy as np
            x, y, w, h = self.band
            rgb = pygame.surfarray.array3d(load_image(self.sheet).subsurface(self.band)).astype(np.int32).sum(axis=2)
            cols, rows = rgb.mean(axis=1), rgb.mean(axis=0)             # 세로줄·가로줄 평균 밝기

            def inset(values):
                n = 0
                while n < len(values) // 4 and values[n] < self.BORDER_DARK:
                    n += 1
                return n + 1 if n else 0                                 # 경계 1px 더 (안티앨리어싱)
            l, r, t = inset(cols), inset(cols[::-1]), inset(rows)
            bt = inset(rows[::-1])
            self._band_trim = pygame.Rect(x + l, y + t, w - l - r, h - t - bt)
        return self._band_trim

    def _draw_band(self, surf, maze, scale):
        area = pygame.Rect(0, 0, maze.cols * scale, self.band_rows * scale)
        src = self._trimmed_band()                                       # 검은 틀 뺀 건물 그림
        k = min(area.width / src.width, area.height / src.height)
        if src.width * k >= area.width * (1 - self.COVER_IF_GAP):
            # 그림이 거의 띠 폭만 하면(명수당·학생회관) 양옆을 채우지 말고 그림을 살짝 키워 폭을 꽉 채움.
            # 좁은 틈을 늘린 색으로 채우면 가로 줄무늬가 생겨서. 넘치는 위쪽(하늘)만 조금 잘림
            k = max(area.width / src.width, area.height / src.height)
            img = self._crop(src, round(src.width * k), round(src.height * k))
            surf.set_clip(area)                                          # 띠 밖으로 넘치는 부분은 안 그림
            surf.blit(img, img.get_rect(midbottom=area.midbottom))
            surf.set_clip(None)
            return
        img = self._crop(src, round(src.width * k), round(src.height * k)).convert_alpha()
        rect = img.get_rect(midbottom=area.midbottom)
        # 1) 양옆 빈 곳: 건물 그림 가장자리(폭의 EDGE_SAMPLE) 배경색을 줄마다 뽑아(중앙값: 가로등 같은 밝은 점 무시)
        #    그 색으로 채움 → 그림 배경색과 그대로 이어짐
        if rect.left > 0:
            import numpy as np
            rgb = pygame.surfarray.array3d(img)                          # (w, h, 3)
            n = max(2, round(rect.width * self.EDGE_SAMPLE))
            fade = min(self.EDGE_FADE, rect.width // 4)                  # 그림 끝이 반투명해지는 부분 밑까지 채움
            for cols, dest in ((rgb[:n], pygame.Rect(0, rect.top, rect.left + fade, rect.height)),
                               (rgb[-n:], pygame.Rect(rect.right - fade, rect.top,
                                                      area.width - rect.right + fade, rect.height))):
                rows = np.median(cols, axis=0)                           # 줄마다 배경색 (h, 3)
                kernel = np.ones(7) / 7                                  # 위아래로 살짝 부드럽게
                rows = np.stack([np.convolve(np.pad(rows[:, c], 3, mode="edge"), kernel, "valid")
                                 for c in range(3)], axis=1)
                column = pygame.surfarray.make_surface(rows[None, :, :].astype(np.uint8))
                surf.blit(pygame.transform.scale(column, dest.size), dest)
            # 2) 건물 그림 좌우 끝을 서서히 투명하게 → 이음새가 안 보이게
            alpha = pygame.surfarray.pixels_alpha(img)
            t = np.arange(fade) / fade
            ramp = (t * t * (3 - 2 * t) * 255).astype(np.uint8)          # smoothstep
            alpha[:fade, :] = np.minimum(alpha[:fade, :], ramp[:, None])
            alpha[-fade:, :] = np.minimum(alpha[-fade:, :], ramp[::-1][:, None])
            del alpha
        if rect.top > area.top:                                          # 위가 비면 맨 윗줄 색으로
            surf.blit(pygame.transform.smoothscale(img.subsurface((0, 0, rect.width, 2)),
                                                   (area.width, rect.top - area.top)), area.topleft)
        surf.blit(img, rect)

    def _draw_lamp(self, surf, cx, bottom, scale):
        glow = pygame.Surface((scale * 2, scale * 2), pygame.SRCALPHA)
        for r, a in ((scale * 0.7, 30), (scale * 0.45, 60), (scale * 0.22, 130)):
            pygame.draw.circle(glow, (*self.LAMP_GLOW, a), (scale, scale), int(r))
        top = bottom - scale * 1.2
        surf.blit(glow, (cx - scale, top - scale))
        pygame.draw.line(surf, (40, 40, 46), (cx, top), (cx, bottom), max(2, scale // 10))
        pygame.draw.circle(surf, self.LAMP_GLOW, (cx, top), max(3, scale // 7))

    def render(self, maze, decor, scale=TILE):
        if load_image(self.sheet) is None:           # 그림이 없으면 기본 테마로
            return super().render(maze, decor, scale)
        surf = pygame.Surface((maze.cols * scale, maze.rows * scale))
        self._draw_band(surf, maze, scale)
        floors = [self._crop(r, scale, scale) for r in self.floors]
        wall = self._crop(self.wall, scale, scale)
        body = self._crop(self.wall_body, scale, scale)
        shadow = pygame.Surface((scale, scale // 4), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 80))

        for y in range(self.band_rows, maze.rows):
            for x in range(maze.cols):
                pos = (x * scale, y * scale)
                if maze.grid[y][x]:
                    above_is_wall = y - 1 >= self.band_rows and maze.grid[y - 1][x]
                    surf.blit(body if above_is_wall else wall, pos)
                else:
                    surf.blit(floors[(x * 7 + y * 13 + (x * y) % 5) % len(floors)], pos)
                    if maze.grid[y - 1][x]:              # 벽 바로 아래 바닥엔 그림자
                        surf.blit(shadow, pos)

        # 아래 담장 가운데는 들어오는 문처럼 비워 보이게
        gate_x = maze.cols // 2
        surf.blit(floors[0], (gate_x * scale, (maze.rows - 1) * scale))
        # 담장 위 가로등
        bottom_row = (maze.rows - 1) * scale
        for x in range(3, maze.cols - 2, 10):                 # 아래 담장: 10칸마다
            if x != gate_x:
                self._draw_lamp(surf, x * scale + scale // 2, bottom_row + scale // 3, scale)
        for y in range(self.band_rows + 3, maze.rows - 2, 8):  # 좌우 담장: 8줄마다
            self._draw_lamp(surf, scale // 2, y * scale + scale, scale)
            self._draw_lamp(surf, (maze.cols - 1) * scale + scale // 2, y * scale + scale, scale)
        return surf


class ZoneTileTheme(CourtyardTheme):
    """CourtyardTheme(위쪽 건물 띠는 그대로)을 상속해서, 마당은 구역별 64px 타일 세트로 그리는 테마.

    타일 세트: assets/tiles/zones/<구역>/ (floor 1장, wall 2~3장, door 2~4장, decor 4장), 목록은 manifest.json
      - 길 칸        : floor_main 한 장으로 통일
      - 벽 칸        : 바로 아래가 길이면 벽 앞면. 첫 번째 벽(기본 벽)을 주로, 나머지 특수 벽은 드물게.
                       양옆이 벽인 앞면은 가끔 문 (보기만 문, 충돌은 벽 그대로)
                       바로 아래도 벽이면(벽의 윗부분) 기본 벽을 어둡게 → 벽이 두꺼워 보이고 앞면과 구분됨
      - 장식(decor)  : 바닥이 포함된 한 칸 타일. Zone이 막다른 길에 놓고 그 칸은 못 지나감
    칸마다 고르는 그림은 좌표로 정해서(같은 칸은 늘 같은 그림) 매 프레임 바뀌지 않는다.
    """
    MANIFEST = "tiles/zones/manifest.json"
    TOP_SHADE = 165             # 벽 윗부분 밝기 (255 = 그대로, 낮을수록 어둡게)

    def __init__(self, key, sheet, band, band_rows, main_wall, special_percent=15, door_percent=12,
                 special_walls=None, floor_mult=None, wall_add=None, wall_shadow=0,
                 decor_cut_water=False):
        """main_wall: 가장 많이 쓸 기본 벽 파일 이름 (manifest 목록은 이름순이라 따로 지정)
        special_percent: 앞면 벽 중 특수 벽 비율 / door_percent: 양옆이 벽인 앞면 중 문 비율
        special_walls: 특수 벽으로 쓸 파일만 고를 때 (같은 이름을 여러 번 넣으면 더 자주 나옴)
        벽·바닥 색이 비슷해서 길이 잘 안 보일 때:
          floor_mult (R,G,B): 바닥·장식에 곱함 (255 = 그대로, 낮을수록 어둡게)
          wall_add (R,G,B): 벽·문에 더함 (밝게)
          wall_shadow: 벽 바로 아래 바닥에 드리우는 그림자 진하기 (0~255)
        decor_cut_water: 장식 그림에 붙어 있는 옛 물(청록색) 배경을 지우고 지금 바닥 위에 올림 (바닥을 바꿨을 때)"""
        self.decor_cut_water = decor_cut_water
        self.floor_mult, self.wall_add, self.wall_shadow = floor_mult, wall_add, wall_shadow
        super().__init__(sheet, band, floors=None, wall=None, wall_body=None, band_rows=band_rows)
        self.key = key
        self.folder = f"tiles/zones/{key}"
        info = _manifest(self.MANIFEST).get("zones", {}).get(key, {})
        names = lambda kind: [f"{kind}/{n}" for n in info.get(kind, [])]
        self.floor_name = (names("floor") or [None])[0]
        walls = names("wall")
        main = f"wall/{main_wall}"
        self.wall_names = [main] + [w for w in walls if w != main] if main in walls else walls
        if special_walls:
            self.wall_names = self.wall_names[:1] + [f"wall/{n}" for n in special_walls]
        self.door_names = names("door")
        self.decor_names = names("decor")           # Zone이 이 이름들로 장식을 배치함
        self.SPECIAL_WALL_PERCENT = special_percent
        self.DOOR_PERCENT = door_percent

    @staticmethod
    def _hash(x, y):
        return (x * 73856093 ^ y * 19349663) % 100

    def _wall_tile(self, maze, decor, x, y):
        """(그림 이름, 윗부분인가)"""
        def solid(cx, cy):          # 벽인가? (장식 칸은 바닥처럼 보이므로 벽으로 치지 않음)
            return (0 <= cx < maze.cols and 0 <= cy < maze.rows
                    and maze.grid[cy][cx] == 1 and (cx, cy) not in decor)
        if not self.wall_names:
            return self.floor_name, True
        main, specials = self.wall_names[0], self.wall_names[1:]
        if y + 1 >= maze.rows or solid(x, y + 1):
            return main, True
        h = self._hash(x, y)
        if (self.door_names and solid(x - 1, y) and solid(x + 1, y) and y > self.band_rows
                and h < self.DOOR_PERCENT):
            return self.door_names[(x + y) % len(self.door_names)], False
        if specials and (h * 7 + 31) % 100 < self.SPECIAL_WALL_PERCENT:
            return specials[(x * 3 + y) % len(specials)], False
        return main, False

    def render(self, maze, decor, scale=TILE):
        if not self.floor_name or load_image(f"{self.folder}/{self.floor_name}") is None:
            return Theme.render(self, maze, decor, scale)    # 타일이 없으면 기본 테마로
        cache = {}

        def tile(name, shade=False, kind="floor"):
            if (name, shade, kind) not in cache:
                img = load_image(f"{self.folder}/{name}")
                img = pygame.transform.smoothscale(img, (scale, scale)).copy() if img else None
                if img and kind == "decor":
                    _cut_teal_water(img)
                if img and kind == "floor" and self.floor_mult:
                    img.fill(self.floor_mult, special_flags=pygame.BLEND_RGB_MULT)
                if img and kind == "wall" and self.wall_add:
                    img.fill(self.wall_add, special_flags=pygame.BLEND_RGB_ADD)
                if img and shade:
                    img.fill((self.TOP_SHADE,) * 3, special_flags=pygame.BLEND_RGB_MULT)
                cache[(name, shade, kind)] = img
            return cache[(name, shade, kind)]

        shadow = None
        if self.wall_shadow:                                  # 위에서 아래로 옅어지는 그림자 띠
            shadow = pygame.Surface((scale, scale // 2), pygame.SRCALPHA)
            for i in range(scale // 2):
                a = int(self.wall_shadow * (1 - i / (scale // 2)) ** 1.5)
                pygame.draw.line(shadow, (0, 0, 0, a), (0, i), (scale, i))

        surf = pygame.Surface((maze.cols * scale, maze.rows * scale))
        if load_image(self.sheet):
            self._draw_band(surf, maze, scale)                # 건물 띠는 부모 클래스 그대로
        floor = tile(self.floor_name)
        for y in range(self.band_rows, maze.rows):
            for x in range(maze.cols):
                pos = (x * scale, y * scale)
                if (x, y) in decor:
                    if self.decor_cut_water:                  # 바닥 위에 배경 지운 장식
                        surf.blit(floor, pos)
                        surf.blit(tile(decor[(x, y)], kind="decor"), pos)
                    else:                                     # 바닥 포함 장식 타일 그대로
                        surf.blit(tile(decor[(x, y)]), pos)
                elif maze.grid[y][x]:
                    name, top = self._wall_tile(maze, decor, x, y)
                    surf.blit(tile(name, shade=top, kind="wall"), pos)
                else:
                    surf.blit(floor, pos)
                if (shadow and not maze.grid[y][x] and y > self.band_rows and maze.grid[y - 1][x]
                        and (x, y - 1) not in decor):
                    surf.blit(shadow, pos)                    # 벽 바로 아래 길에 그림자
        return surf


class ImageTheme(Theme):
    """미로 그림 한 장을 통째로 배경으로 쓰는 테마. 벽/길 판정은 맵 파일이 따로 담당."""

    def __init__(self, image_file):
        self.image_file = image_file

    def render(self, maze, decor, scale=TILE):
        img = load_image(self.image_file)
        if img is None:                              # 그림이 없으면 기본 테마로
            return super().render(maze, decor, scale)
        return pygame.transform.smoothscale(img, (maze.cols * scale, maze.rows * scale))


# ---------------------------------------------------------------------
# 건물별 테마
# ---------------------------------------------------------------------

def _cut_teal_water(img):
    """장식 그림에서 채도 높은 청록색(물) 픽셀만 투명하게. 돌·풀·꽃처럼 탁한 색은 남는다."""
    rgb = pygame.surfarray.pixels3d(img)
    alpha = pygame.surfarray.pixels_alpha(img)
    r, g, b = (rgb[..., i].astype("int32") for i in range(3))
    alpha[(r < 32) & (b > r + 28) & (b >= g - 4) & (g > r + 20)] = 0
    del rgb, alpha


def _manifest(rel_path):
    """assets/ 기준 manifest.json 읽기 (없으면 빈 dict)."""
    path = os.path.join(ASSET_DIR, rel_path)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# 맵 파일에서 장식 기호 -> 이름 (장식은 벽처럼 지나갈 수 없음, 기본 테마는 작은 사각형으로 그림)
DECOR_SYMBOLS = {"P": "plant", "T": "table", "L": "lamp"}

# "건물 + 앞마당" 테마: 참고 그림(campus_mazes.png, 1536x1024, 건물 4개가 2x2로 있음)에서 잘라 씀
# 좌표는 (x, y, 너비, 높이). 왼쪽 위 = 학생회관, 오른쪽 위 = 명수당, 왼쪽 아래 = 도서관, 오른쪽 아래 = 기숙사
CAMPUS_SHEET = "tiles/campus_mazes.png"
LIBRARY_COURTYARD = CourtyardTheme(
    CAMPUS_SHEET, band=(0, 512, 768, 215),
    floors=[(134, 751, 32, 32), (162, 879, 32, 32), (70, 819, 32, 32)],
    wall=(360, 762, 32, 30), wall_body=(432, 796, 24, 28), band_rows=BUILDING_BAND_ROWS)
DORMITORY_COURTYARD = CourtyardTheme(
    CAMPUS_SHEET, band=(768, 512, 768, 215),
    floors=[(980, 803, 32, 32), (1308, 751, 32, 32)],
    wall=(872, 814, 32, 36), wall_body=(950, 840, 22, 32), band_rows=BUILDING_BAND_ROWS)
MYEONGSUDANG_COURTYARD = CourtyardTheme(
    CAMPUS_SHEET, band=(768, 0, 768, 140),
    floors=[(1176, 422, 32, 32), (1172, 418, 32, 32)],
    wall=(1352, 170, 32, 30), wall_body=(1416, 200, 20, 32), band_rows=BUILDING_BAND_ROWS)
STUDENT_HALL_COURTYARD = CourtyardTheme(
    CAMPUS_SHEET, band=(0, 0, 768, 130),
    floors=[(134, 751, 32, 32), (162, 879, 32, 32), (70, 819, 32, 32)],   # 도서관과 같은 돌바닥
    wall=(160, 168, 32, 32), wall_body=(136, 200, 24, 24), band_rows=BUILDING_BAND_ROWS)

# 64px 타일 세트 (assets/tiles/zones/, manifest.json) + 위쪽 건물 띠는 참고 그림에서
LIBRARY_TILES = ZoneTileTheme(
    "library", CAMPUS_SHEET, band=(0, 512, 768, 215), band_rows=BUILDING_BAND_ROWS,
    main_wall="bookshelf.png")
DORMITORY_TILES = ZoneTileTheme(                      # README: 기숙사 벽은 약 70%가 방문(301~310호)
    "dorm", CAMPUS_SHEET, band=(768, 512, 768, 215), band_rows=BUILDING_BAND_ROWS,
    main_wall="dorm_wall.png", door_percent=70)
MYEONGSUDANG_TILES = ZoneTileTheme(                   # 이끼·연꽃 석벽이 섞이도록 특수 벽 비율 높게
    "pond", CAMPUS_SHEET, band=(768, 0, 768, 140), band_rows=BUILDING_BAND_ROWS,
    main_wall="underwater_stone.png", special_percent=45,
    wall_add=(30, 32, 28), wall_shadow=150,            # 석벽은 밝게 + 벽 아래 그림자 (새 바닥은 원래 어두움)
    decor_cut_water=True)                               # 장식의 옛 물 배경 지우고 새 바닥 위에
STUDENT_HALL_TILES = ZoneTileTheme(
    "student_hall", CAMPUS_SHEET, band=(0, 0, 768, 130), band_rows=BUILDING_BAND_ROWS,
    main_wall="hall_wall.png")

DEFAULT_THEME = Theme()
# 구역 번호 -> 테마. 없는 구역은 DEFAULT_THEME
# (TileTheme·ImageTheme 클래스도 남아 있음: 타일 폴더나 미로 그림을 주면 여기에 등록해서 쓸 수 있음)
ZONE_THEMES = {
    1: LIBRARY_TILES,              # 도서관 (왼쪽 위)
    2: STUDENT_HALL_TILES,         # 학생회관 (오른쪽 위)
    3: MYEONGSUDANG_TILES,         # 명수당 (왼쪽 아래)
    4: DORMITORY_TILES,            # 기숙사 (오른쪽 아래)
    # (예전 참고 그림 조각 버전: LIBRARY_COURTYARD 등도 남아 있음)
}
