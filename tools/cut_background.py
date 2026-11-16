"""건물 그림 한 장의 배경(검정 / 흰색·체크무늬)을 가장자리부터 투명하게 지우고 그림 크기에 맞게 잘라 저장.

사용법 (maze_runner 폴더에서):
    python tools/cut_background.py 그림.webp assets/buildings/library.png
    옵션: --dark=40   검은 배경으로 칠 어두움 기준 (R+G+B, 기본 40)
          --light=600 흰색·밝은 회색 체크무늬 배경 기준 (R+G+B 이상 + 무채색, 기본 600)
          --no-outline 지운 뒤 남은 검은 외곽선 한 겹 벗기기
- 이미 투명 배경인 그림은 그대로 두고 잘라내기만 함
- 배경 종류(검정/밝은색)는 왼쪽 위 모서리 색으로 자동 판단
"""
import os
import sys
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut_sprite_sheet import remove_fringe   # noqa: E402  (같은 tools 폴더)


def flood_clear(img, is_bg):
    """가장자리에서 시작해 is_bg(r, g, b)인 픽셀을 따라가며 투명하게."""
    W, H = img.get_size()
    rgb = pygame.surfarray.pixels3d(img)
    alpha = pygame.surfarray.pixels_alpha(img)
    seen = bytearray(W * H)
    q = deque([(x, y) for x in range(W) for y in (0, H - 1)] + [(x, y) for y in range(H) for x in (0, W - 1)])
    while q:
        x, y = q.popleft()
        i = y * W + x
        if seen[i]:
            continue
        seen[i] = 1
        if alpha[x, y] != 0 and not is_bg(int(rgb[x, y, 0]), int(rgb[x, y, 1]), int(rgb[x, y, 2])):
            continue
        alpha[x, y] = 0
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and not seen[ny * W + nx]:
                q.append((nx, ny))
    del rgb, alpha


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    src, dst = args
    opt = {a.split("=")[0]: a.split("=")[1] for a in sys.argv if a.startswith("--") and "=" in a}
    dark, light = int(opt.get("--dark", 40)), int(opt.get("--light", 600))
    pygame.init()
    pygame.display.set_mode((1, 1))
    img = pygame.image.load(src).convert_alpha()
    r, g, b, a = img.get_at((0, 0))
    if a != 0:
        if r + g + b < 200:     # 검은 배경
            flood_clear(img, lambda r, g, b: r + g + b < dark)
        else:                   # 흰색·밝은 회색 체크무늬 배경
            flood_clear(img, lambda r, g, b: r + g + b >= light and max(r, g, b) - min(r, g, b) < 18)
        if "--no-outline" in sys.argv:
            img = remove_fringe(img)
    img = img.subsurface(img.get_bounding_rect(min_alpha=20)).copy()
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    pygame.image.save(img, dst)
    print("저장:", dst, img.get_size())


if __name__ == "__main__":
    main()
