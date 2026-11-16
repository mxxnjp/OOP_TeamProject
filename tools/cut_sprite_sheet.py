"""캐릭터 앞/옆/뒤 그림 한 장(가로로 4개: 앞, 왼쪽, 뒤, 오른쪽)을 방향별 PNG 4장으로 자르는 도구.

사용법 (maze_runner 폴더에서):
    python tools/cut_sprite_sheet.py 그림파일.png player boy
    python tools/cut_sprite_sheet.py 그림파일.webp player girl
    python tools/cut_sprite_sheet.py 그림파일.png monsters guard --three   (앞, 옆, 뒤 3개뿐일 때: 오른쪽은 좌우 반전)

    옵션: --dark=12 (배경으로 칠 어두움 기준, 기본 40. 눈·머리처럼 어두운 부분이 뚫리면 낮추기)
          --no-outline (캐릭터 바깥 검은 테두리를 벗김)

결과: assets/<폴더>/<이름>_down.png, _left.png, _up.png, _right.png
- 검은(또는 아주 어두운) 배경은 가장자리부터 투명하게 지움 (이미 투명 배경이면 그대로)
- 4장을 같은 크기 캔버스에 발 위치를 맞춰 저장 → 방향을 바꿔도 크기가 안 변함
"""
import os
import sys
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame


def cut_background(img, dark=40):
    W, H = img.get_size()
    rgb = pygame.surfarray.pixels3d(img)
    alpha = pygame.surfarray.pixels_alpha(img)
    if alpha[0, 0] == 0 and alpha[W - 1, H - 1] == 0:      # 이미 투명 배경
        del rgb, alpha
        return img
    seen = bytearray(W * H)
    q = deque([(x, y) for x in range(W) for y in (0, H - 1)] + [(x, y) for y in range(H) for x in (0, W - 1)])
    while q:
        x, y = q.popleft()
        i = y * W + x
        if seen[i]:
            continue
        seen[i] = 1
        if int(rgb[x, y, 0]) + int(rgb[x, y, 1]) + int(rgb[x, y, 2]) >= dark:
            continue
        alpha[x, y] = 0
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and not seen[ny * W + nx]:
                q.append((nx, ny))
    del rgb, alpha
    return img


def remove_fringe(img, passes=2, dark=150):
    """배경을 지운 뒤 가장자리에 남은 검은 테두리(외곽선)를 한 겹씩 벗김."""
    import numpy as np
    rgb = pygame.surfarray.pixels3d(img)
    alpha = pygame.surfarray.pixels_alpha(img)
    for _ in range(passes):
        clear = alpha == 0
        edge = np.zeros_like(clear)
        edge[1:, :] |= clear[:-1, :]
        edge[:-1, :] |= clear[1:, :]
        edge[:, 1:] |= clear[:, :-1]
        edge[:, :-1] |= clear[:, 1:]
        bright = rgb.astype(np.int32).sum(axis=2)
        alpha[edge & ~clear & (bright < dark)] = 0
    del rgb, alpha
    return img


def split_columns(img, min_gap=25, min_width=40):
    W, H = img.get_size()
    alpha = pygame.surfarray.array_alpha(img)
    filled = [(alpha[x] > 60).any() for x in range(W)]
    pieces, start, gap = [], None, 0
    for x, f in enumerate(filled + [False] * min_gap):
        if f:
            start = x if start is None else start
            gap, end = 0, x
        elif start is not None:
            gap += 1
            if gap >= min_gap:
                if end - start >= min_width:
                    sub = img.subsurface((start, 0, end - start + 1, H))
                    pieces.append(sub.subsurface(sub.get_bounding_rect(min_alpha=60)).copy())
                start = None
    return pieces


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    src, folder, name = sys.argv[1:4]
    three = "--three" in sys.argv
    pygame.init()
    pygame.display.set_mode((1, 1))
    dark = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--dark=")), 40)
    img = cut_background(pygame.image.load(src).convert_alpha(), dark)
    if "--no-outline" in sys.argv:
        img = remove_fringe(img)
    views = split_columns(img)
    need = 3 if three else 4
    if len(views) != need:
        sys.exit(f"그림 {len(views)}개를 찾았어요. {need}개여야 합니다 (간격이 너무 좁으면 min_gap을 줄이세요).")
    if three:
        views.append(pygame.transform.flip(views[1], True, False))
        order = {"down": views[0], "left": views[1], "up": views[2], "right": views[3]}
    else:
        order = {"down": views[0], "left": views[1], "up": views[2], "right": views[3]}
    W = max(v.get_width() for v in order.values())
    H = max(v.get_height() for v in order.values())
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", folder)
    os.makedirs(out_dir, exist_ok=True)
    for d, v in order.items():
        canvas = pygame.Surface((W, H), pygame.SRCALPHA)
        canvas.blit(v, v.get_rect(midbottom=(W // 2, H)))
        path = os.path.join(out_dir, f"{name}_{d}.png")
        pygame.image.save(canvas, path)
        print("저장:", path)


if __name__ == "__main__":
    main()
