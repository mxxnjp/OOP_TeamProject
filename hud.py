"""상단 HUD(목숨, 체력, 인벤토리, 낮/밤, 전체 지도)와 공용 그리기 함수."""
import pygame

from themes import load_sprite, load_image

from settings import (SCREEN_W, SCREEN_H, HUD_HEIGHT, ZONE_LAYOUT, PLAYER_MAX_HP, FINAL_ZONE_ID, FONT_NAMES,
                      ZONE_NAMES, BOSS_NAME, ITEM_SPRITES, MAIN_BACKGROUND, CENTER_TONE_BG,
                      HUD_BG, WHITE, GRAY, RED, DARK_RED, GREEN, GOLD, YELLOW,
                      HOME_COLOR, PURPLE)


def draw_heart(surf, x, y, size, filled):
    color = RED if filled else (70, 40, 40)
    r = size // 4
    pygame.draw.circle(surf, color, (x + r, y + r), r)
    pygame.draw.circle(surf, color, (x + 3 * r, y + r), r)
    pygame.draw.polygon(surf, color, [(x, y + r), (x + size, y + r), (x + size // 2, y + size - 2)])


def draw_text(surf, font, text, pos, color=WHITE, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
    surf.blit(img, rect)
    return rect


def _slot_icon(surf, slot_rect, key, owned):
    """인벤토리 칸 왼쪽에 아이템 그림. 아직 없는 아이템은 흐리게. 그림이 없으면 False."""
    img = load_sprite(ITEM_SPRITES.get(key), 28)
    if not img:
        return False
    if not owned:
        img = img.copy()
        img.set_alpha(70)
    surf.blit(img, img.get_rect(center=(slot_rect.x + 26, slot_rect.centery + 2)))
    return True


def draw_minimap(surf, rect, current_zone_id, is_night):
    """2x2 구역 + 가운데 집. 현재 위치를 강조."""
    pygame.draw.rect(surf, (40, 40, 50), rect, border_radius=4)
    cw, ch = rect.width // 2, rect.height // 2
    for zid, (lx, ly) in ZONE_LAYOUT.items():
        r = pygame.Rect(rect.x + lx * cw + 3, rect.y + ly * ch + 3, cw - 6, ch - 6)
        active = zid == current_zone_id
        pygame.draw.rect(surf, YELLOW if active else (70, 90, 70), r, 0 if active else 2, border_radius=3)
    home_color = YELLOW if current_zone_id is None else HOME_COLOR
    pygame.draw.circle(surf, home_color, rect.center, 9)
    if is_night:
        pygame.draw.circle(surf, PURPLE, (rect.right - 6, rect.y + 6), 4)


class HudSkin:
    """디자인 그림(assets/ui/hud_design.png, 2000x667)을 HUD 배경으로 쓰고, 그 위에 실제 값을 그린다.

    그림 속의 예시 글자·하트·아이콘 자리는 그 칸 안쪽 색으로 지운 뒤(빈 틀만 남김) 0.4배로 줄여 쓴다.
    좌표는 모두 원본 그림 기준 (x, y). 화면 좌표는 S()로 바꾼다.
    """
    FILE = "ui/hud_design.png"
    STRIP = (0, 210, 2000, 240)                     # 그림에서 HUD로 쓸 띠 (0.4배 -> 800x96)
    K = SCREEN_W / 2000
    PANEL_CLEAR = ((238, 250, 418, 165), (35, 37, 55))
    WEAPON_PILLS = [(720, 258, 918, 330), (935, 258, 1143, 330), (1162, 258, 1365, 330)]
    ZONE_PILLS = [(718, 357, 918, 428), (935, 357, 1150, 428), (1167, 357, 1378, 428), (1395, 357, 1612, 428)]
    PILL_COLOR = (39, 40, 60)
    MAP_INNER = (1710, 246, 262, 184)

    def __init__(self):
        self.base = None
        self.loaded = False
        self.font_label = pygame.font.SysFont(FONT_NAMES, 13, bold=True)
        self.font_text = pygame.font.SysFont(FONT_NAMES, 12, bold=True)

    @classmethod
    def S(cls, x, y):
        """원본 그림 좌표 -> 화면 좌표"""
        return x * cls.K, (y - cls.STRIP[1]) * cls.K

    @classmethod
    def R(cls, x0, y0, x1, y1):
        (a, b), (c, d) = cls.S(x0, y0), cls.S(x1, y1)
        return pygame.Rect(round(a), round(b), round(c - a), round(d - b))

    def load(self):
        """처음 한 번: 그림을 잘라 예시 내용을 지우고 HUD 크기로 줄여 둔다. 그림이 없으면 None."""
        if not self.loaded:
            self.loaded = True
            img = load_image(self.FILE)
            if img:
                strip = img.subsurface(self.STRIP).copy()
                oy = self.STRIP[1]

                def clear(x, y, w, h, color):
                    strip.fill(color, (x, y - oy, w, h))

                (x, y, w, h), color = self.PANEL_CLEAR
                clear(x, y, w, h, color)
                for x0, y0, x1, y1 in self.WEAPON_PILLS:   # 번호 동그라미(1·2·3)는 남기고 오른쪽만
                    clear(x0 + 60, y0 + 10, x1 - x0 - 80, y1 - y0 - 18, self.PILL_COLOR)
                for x0, y0, x1, y1 in self.ZONE_PILLS:
                    clear(x0 + 20, y0 + 12, x1 - x0 - 40, y1 - y0 - 24, self.PILL_COLOR)
                strip = _clear_black(strip)                 # 검은 바탕은 투명 → 뒤의 배경 그림이 보이게
                self.base = pygame.transform.smoothscale(strip, (SCREEN_W, round(self.STRIP[3] * self.K)))
        return self.base

    @staticmethod
    def _key_icon(surf, cx, cy, color):
        pygame.draw.circle(surf, color, (cx - 4, cy), 4, 2)
        pygame.draw.line(surf, color, (cx, cy), (cx + 7, cy), 2)
        pygame.draw.line(surf, color, (cx + 5, cy), (cx + 5, cy + 3), 2)

    def draw(self, surf, game, current_zone_id):
        p, inv, S = game.player, game.player.inventory, self.S
        bg = screen_background()                       # HUD 뒤에도 메인 배경 그림 (없으면 검정)
        if bg:
            surf.blit(bg, (0, 0), (0, 0, SCREEN_W, HUD_HEIGHT))
        else:
            surf.fill((0, 0, 0), (0, 0, SCREEN_W, HUD_HEIGHT))
        surf.blit(self.base, (0, 0))

        # 왼쪽 패널: 목숨 / 체력 / 낮·밤
        draw_text(surf, self.font_label, "목숨", S(252, 266), WHITE)
        for i in range(game.max_lives):
            x, y = S(340 + i * 55, 264)
            draw_heart(surf, int(x), int(y), 15, i < p.lives)
        draw_text(surf, self.font_label, "체력", S(252, 314), WHITE)
        for i in range(PLAYER_MAX_HP):
            x, y = S(342 + i * 27, 316)
            pygame.draw.rect(surf, GREEN if i < p.hp else DARK_RED, (int(x), int(y), 9, 10), border_radius=2)
        if current_zone_id == FINAL_ZONE_ID:
            phase, color = f"최종 스테이지 - vs {BOSS_NAME}", (205, 150, 255)
        elif game.is_night:
            phase, color = f"밤 {game.day}일차 - 괴물을 쓰러뜨려라", (205, 150, 255)
        else:
            mm, ss = divmod(int(max(0, game.day_timer)), 60)
            phase = f"낮 {game.day}일차 - 밤까지 {mm:02d}:{ss:02d}"
            color = RED if game.day_timer <= 10 else YELLOW
        draw_text(surf, self.font_text, phase, S(252, 366), color)

        # 무기·물약 칸 (그림은 우리 게임의 창·활·물약 그림)
        slots = [("spear", inv.weapons.get("spear")), ("bow", inv.weapons.get("bow")), ("potion", None)]
        for (key, weapon), (x0, y0, x1, y1) in zip(slots, self.WEAPON_PILLS):
            mid = (y0 + y1) / 2
            owned = inv.potions > 0 if key == "potion" else weapon is not None
            icon = load_sprite(ITEM_SPRITES.get(key), 22)
            if icon and not owned:
                icon = icon.copy()
                icon.set_alpha(80)
            if key == "potion":
                text = f"x{inv.potions}"
            else:
                text = weapon.label().replace("창", "").replace("활", "").strip() or "장착" if weapon else "없음"
            img = self.font_text.render(text, True, WHITE if owned else (150, 150, 165))
            # 번호 동그라미 오른쪽 ~ 칸 오른쪽 끝 사이 가운데에 [아이콘 + 글자]를 한 묶음으로
            (left, cy), (right, _) = S(x0 + 66, mid), S(x1 - 26, mid)
            gap = 3
            width = (icon.get_width() + gap if icon else 0) + img.get_width()
            x = round((left + right - width) / 2)
            if icon:
                surf.blit(icon, icon.get_rect(midleft=(x, cy)))
                x += icon.get_width() + gap
            surf.blit(img, img.get_rect(midleft=(x, cy)))
            if weapon is not None and inv.current == weapon.name:          # 들고 있는 무기 강조
                pygame.draw.rect(surf, YELLOW, self.R(x0, y0, x1, y1).inflate(2, 2), 2, border_radius=14)

        # 건물 키 칸 4개
        for (zid, name), (x0, y0, x1, y1) in zip(ZONE_NAMES.items(), self.ZONE_PILLS):
            got = inv.has_key_for(zid)
            color = GOLD if got else (150, 150, 165)
            cx, cy = S(x0 + 42, (y0 + y1) / 2)
            self._key_icon(surf, int(cx), int(cy), color)
            img = self.font_text.render(name, True, color)              # 열쇠 아이콘 오른쪽 남은 칸 가운데
            surf.blit(img, img.get_rect(center=S((x0 + 64 + x1 - 18) / 2, (y0 + y1) / 2)))
            if zid == current_zone_id:                                       # 지금 있는 건물
                pygame.draw.rect(surf, (140, 200, 255), self.R(x0, y0, x1, y1).inflate(2, 2), 2,
                                 border_radius=14)

        # 전체 지도 (오른쪽 틀 안)
        x, y, w, h = self.MAP_INNER
        draw_minimap(surf, self.R(x, y, x + w, y + h), current_zone_id, game.is_night)


    # ---------------- 메뉴(ESC 일시정지 등)에서 HUD와 같은 틀을 쓰기 위한 조각 ----------------
    PILL = (1395, 355, 218, 75)                  # '설정' 알약 버튼 틀
    PILL_CAP = 38                                # 알약 양 끝 둥근 부분 너비

    def _design(self):
        return load_image(self.FILE)

    def panel(self, w, h, k=0.7):
        """알약 버튼 틀(돌 테두리)을 9조각으로 늘려 w x h 패널로. 그림이 없으면 None."""
        src = self._pill_source()
        if src is None:
            return None
        return _nine_slice(src, (self.PILL_CAP, 30, self.PILL_CAP, 30), w, h, k)

    def _pill_source(self):
        img = self._design()
        if img is None:
            return None
        pw, ph = self.PILL[2:]
        src = img.subsurface(self.PILL).copy()
        src.fill(self.PILL_COLOR, (20, 12, pw - 40, ph - 24))       # 아이콘·글자 지우기
        return _clear_black(src)

    def pill(self, w, h):
        """알약 모양 버튼 틀을 w x h로 (둥근 끝은 비율 유지, 가운데만 늘림)."""
        src = self._pill_source()
        if src is None:
            return None
        pw, ph = self.PILL[2:]
        k = h / ph
        cap = round(self.PILL_CAP * k)
        src = pygame.transform.smoothscale(src, (round(pw * k), h))
        sw = src.get_width()
        out = pygame.Surface((w, h), pygame.SRCALPHA)
        out.blit(src, (0, 0), (0, 0, cap, h))
        out.blit(pygame.transform.smoothscale(src.subsurface((cap, 0, sw - 2 * cap, h)), (w - 2 * cap, h)),
                 (cap, 0))
        out.blit(src, (w - cap, 0), (sw - cap, 0, cap, h))
        return out


def _nine_slice(src, insets, w, h, k):
    """그림을 9조각(모서리 4 + 변 4 + 가운데)으로 나눠 모서리 모양은 그대로, 나머지만 늘려 w x h로."""
    l, t, r, b = insets
    sw, sh = src.get_size()
    L, T, R, B = (round(v * k) for v in insets)
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    cols = [(0, l, 0, L), (l, sw - r, L, w - R), (sw - r, sw, w - R, w)]
    rows = [(0, t, 0, T), (t, sh - b, T, h - B), (sh - b, sh, h - B, h)]
    for sx0, sx1, dx0, dx1 in cols:
        for sy0, sy1, dy0, dy1 in rows:
            piece = src.subsurface((sx0, sy0, sx1 - sx0, sy1 - sy0))
            out.blit(pygame.transform.smoothscale(piece, (dx1 - dx0, dy1 - dy0)), (dx0, dy0))
    return out


def _clear_black(surf, dark=24):
    """디자인 그림의 검은 바탕을 투명하게 (틀 바깥 모서리)."""
    surf = surf.convert_alpha()
    rgb = pygame.surfarray.pixels3d(surf)
    alpha = pygame.surfarray.pixels_alpha(surf)
    alpha[rgb.astype('int32').sum(axis=2) < dark] = 0
    del rgb, alpha
    return surf


class CenterMapSkin:
    """과방(메인) 지도 디자인 그림(assets/ui/center_design.png, 1669x942)에서 조각을 잘라 쓰는 담당.

    - 배경   : 그림의 HUD 아래 부분을 흐리고 어둡게 해서 깔기 (분위기만)
    - 건물   : 그림 속 건물(가로등·나무 포함)을 잘라 가장자리를 부드럽게 지운 것 → 버튼 그림으로 사용
    - 과방   : 가운데 과방 그림 (이름·'안전지대·회복' 표시 포함)
    - 이름표 : 건물 이름표 틀(알약 모양)만 남기고 글자는 게임이 실제 상태로 써 넣음
    좌표는 모두 원본 그림 기준 (x, y, w, h). 화면 위치는 to_screen()으로 바꾼다.
    """
    FILE = "ui/center_design.png"
    TOP = 180                                       # 이 위는 그림 속 HUD라 안 씀
    CENTER = (680, 465, 320, 225)                   # 가운데 과방
    LABEL = (262, 203, 350, 58)                     # '1. 도서관 - ...' 이름표 틀
    LABEL_CAP = 40                                  # 이름표 양 끝(화살표 모양) 너비
    LABEL_FILL = (36, 36, 47)                       # 이름표 안쪽 색 (글자 지울 때)
    BUILDING_SCALE = 0.58
    CENTER_SCALE = 0.62
    LABEL_HEIGHT = 34

    def __init__(self):
        self.img = None
        self.loaded = False

    def load(self):
        if not self.loaded:
            self.loaded = True
            self.img = load_image(self.FILE)
        return self.img

    def to_screen(self, x, y):
        """원본 그림 좌표 -> 화면 좌표 (가로·세로를 HUD 아래 놀이 영역에 맞춤)"""
        W, H = self.img.get_size()
        return (x * SCREEN_W / W, HUD_HEIGHT + (y - self.TOP) * (SCREEN_H - HUD_HEIGHT) / (H - self.TOP))

    def background(self):
        W, H = self.img.get_size()
        size = (SCREEN_W, SCREEN_H - HUD_HEIGHT)
        bg = self.img.subsurface((0, self.TOP, W, H - self.TOP))
        bg = pygame.transform.smoothscale(bg, (size[0] // 12, size[1] // 12))     # 크게 흐리기
        bg = pygame.transform.smoothscale(bg, size)
        bg.fill((115, 115, 130), special_flags=pygame.BLEND_RGB_MULT)            # 어둡게
        return bg

    def piece(self, rect, scale, feather=14):
        """그림 조각을 잘라 가장자리 feather px를 서서히 투명하게 하고 scale배로."""
        import numpy as np
        part = self.img.subsurface(rect).convert_alpha()
        w, h = part.get_size()
        xs = np.minimum(np.arange(w), np.arange(w)[::-1])
        ys = np.minimum(np.arange(h), np.arange(h)[::-1])
        edge = np.minimum.outer(xs, ys)                      # 가장자리까지 거리 (w x h)
        alpha = pygame.surfarray.pixels_alpha(part)
        alpha[:] = (np.clip(edge / feather, 0, 1) * 255).astype(np.uint8)
        del alpha
        return pygame.transform.smoothscale(part, (round(w * scale), round(h * scale)))

    def building(self, image, rect, tone, fit=1.08, feather=16, scale=None):
        """건물 그림을 디자인 그림 속 그 건물 자리(rect) 크기에 맞추고(비율 유지),
        색감(tone = (평균, 표준편차))을 디자인 그림에 맞추고 가장자리를 살짝 부드럽게."""
        import numpy as np
        x, y, w, h = rect
        scale = scale or self.BUILDING_SCALE
        box_w, box_h = w * scale * fit, h * scale * fit
        k = min(box_w / image.get_width(), box_h / image.get_height())
        img = pygame.transform.smoothscale(image, (round(image.get_width() * k), round(image.get_height() * k)))
        img = match_tone(img.convert_alpha(), *tone)          # 디자인 그림 속 건물과 같은 색감으로
        iw, ih = img.get_size()
        xs = np.minimum(np.arange(iw), np.arange(iw)[::-1])
        ys = np.minimum(np.arange(ih), np.arange(ih)[::-1])
        alpha = pygame.surfarray.pixels_alpha(img)
        edge = (np.clip(np.minimum.outer(xs, ys) / feather, 0, 1) * 255).astype(np.uint8)
        alpha[:] = np.minimum(alpha, edge)
        del alpha
        return img

    def tone_of(self, rect):
        """디자인 그림 속 rect 부분의 색 분포 (채널별 평균, 표준편차) → match_tone의 목표로 씀."""
        import numpy as np
        pix = pygame.surfarray.array3d(self.img.subsurface(rect)).reshape(-1, 3).astype(np.float32)
        return tuple(pix.mean(axis=0)), tuple(pix.std(axis=0))

    def center_point(self, rect):
        x, y, w, h = rect
        return self.to_screen(x + w / 2, y + h / 2)

    def label(self, text_img):
        """이름표 틀을 글자 길이에 맞춰 늘린 것 (양 끝 모양 유지) + 가운데에 글자."""
        if not hasattr(self, "_label_src"):
            x, y, w, h = self.LABEL
            src = self.piece(self.LABEL, 1.0, feather=3)
            src.fill(self.LABEL_FILL + (255,), (self.LABEL_CAP - 8, 11, w - 2 * self.LABEL_CAP + 16, h - 22))
            k = self.LABEL_HEIGHT / h
            self._label_src = pygame.transform.smoothscale(src, (round(w * k), self.LABEL_HEIGHT))
            self._label_cap = round(self.LABEL_CAP * k)
        src, cap, h = self._label_src, self._label_cap, self.LABEL_HEIGHT
        sw = src.get_width()
        w = text_img.get_width() + 2 * cap + 8
        out = pygame.Surface((w, h), pygame.SRCALPHA)
        out.blit(src, (0, 0), (0, 0, cap, h))
        out.blit(pygame.transform.smoothscale(src.subsurface((cap, 0, sw - 2 * cap, h)), (w - 2 * cap, h)),
                 (cap, 0))
        out.blit(src, (w - cap, 0), (sw - cap, 0, cap, h))
        out.blit(text_img, text_img.get_rect(center=(w // 2, h // 2)))
        return out


_BACKGROUND = []


def match_tone(img, mean, std, strength=1.0):
    """그림의 색 분포를 목표(채널별 평균·표준편차)에 맞춘 새 그림 (투명한 부분은 계산에서 뺌).
    strength: 0 = 그대로, 1 = 완전히 맞춤."""
    import numpy as np
    out = img.convert_alpha() if img.get_flags() & pygame.SRCALPHA else img.copy()
    rgb = pygame.surfarray.pixels3d(out)
    alpha = pygame.surfarray.pixels_alpha(out) if out.get_flags() & pygame.SRCALPHA else None
    pix = rgb.reshape(-1, 3).astype(np.float32)
    used = pix[alpha.reshape(-1) > 128] if alpha is not None else pix
    m0, s0 = used.mean(axis=0), used.std(axis=0) + 1e-3
    mapped = (pix - m0) / s0 * np.array(std, np.float32) + np.array(mean, np.float32)
    pix = pix * (1 - strength) + mapped * strength
    rgb[:] = np.clip(pix, 0, 255).astype(np.uint8).reshape(rgb.shape)
    del rgb, alpha
    return out


def screen_background():
    """메인 배경 그림(settings.MAIN_BACKGROUND)을 화면 전체(800x640)를 꽉 채우게 맞춘 것. 없으면 None.
    비율이 달라서 세로에 맞추고 좌우 가운데만 씀."""
    if not _BACKGROUND:
        img = load_image(MAIN_BACKGROUND)
        if img:
            k = max(SCREEN_W / img.get_width(), SCREEN_H / img.get_height())
            big = pygame.transform.smoothscale(img, (round(img.get_width() * k), round(img.get_height() * k)))
            img = big.subsurface(pygame.Rect(0, 0, SCREEN_W, SCREEN_H).move(
                (big.get_width() - SCREEN_W) // 2, (big.get_height() - SCREEN_H) // 2)).copy()
            img = match_tone(img, *CENTER_TONE_BG)          # 메인 디자인 그림의 배경 색감으로
        _BACKGROUND.append(img)
    return _BACKGROUND[0]


_CENTER_SKIN = None


def center_map_skin():
    global _CENTER_SKIN
    if _CENTER_SKIN is None:
        _CENTER_SKIN = CenterMapSkin()
    return _CENTER_SKIN


_SKIN = None


def hud_skin():
    """HUD 디자인 그림 담당 객체 (한 번만 만듦)."""
    global _SKIN
    if _SKIN is None:
        _SKIN = HudSkin()
    return _SKIN


def draw_hud(surf, game, current_zone_id=None):
    """디자인 그림이 있으면 그 HUD를, 없으면 기본 HUD를 그린다."""
    skin = hud_skin()
    if skin.load():
        skin.draw(surf, game, current_zone_id)
    else:
        draw_hud_basic(surf, game, current_zone_id)


def draw_hud_basic(surf, game, current_zone_id=None):
    """그림 없이 도형만으로 그리는 기본 HUD."""
    p = game.player
    inv = p.inventory
    f = game.font_small
    pygame.draw.rect(surf, HUD_BG, (0, 0, SCREEN_W, HUD_HEIGHT))
    pygame.draw.line(surf, (60, 60, 70), (0, HUD_HEIGHT - 1), (SCREEN_W, HUD_HEIGHT - 1))

    # 목숨
    draw_text(surf, f, "목숨", (12, 10))
    for i in range(game.max_lives):
        draw_heart(surf, 56 + i * 24, 11, 18, i < p.lives)

    # 체력 10칸
    draw_text(surf, f, "체력", (12, 38))
    for i in range(PLAYER_MAX_HP):
        color = GREEN if i < p.hp else DARK_RED
        pygame.draw.rect(surf, color, (56 + i * 17, 41, 14, 14), border_radius=2)

    # 낮 / 밤 / 최종 스테이지
    if current_zone_id == FINAL_ZONE_ID:
        draw_text(surf, f, f"최종 스테이지 - vs {BOSS_NAME}", (12, 66), PURPLE)
    elif game.is_night:
        draw_text(surf, f, f"밤 {game.day}일차  - 괴물을 쓰러뜨려라", (12, 66), PURPLE)
    else:
        mm, ss = divmod(int(max(0, game.day_timer)), 60)
        color = RED if game.day_timer <= 10 else YELLOW   # 10초 남으면 빨간색 경고
        draw_text(surf, f, f"낮 {game.day}일차  밤까지 {mm:02d}:{ss:02d}", (12, 66), color)

    # 인벤토리 슬롯
    slots = [("1", inv.weapons.get("spear"), "창"), ("2", inv.weapons.get("bow"), "활")]
    x = 260
    for key_label, weapon, name in slots:
        r = pygame.Rect(x, 10, 92, 40)
        selected = weapon is not None and inv.current == weapon.name
        pygame.draw.rect(surf, (50, 50, 60), r, border_radius=5)
        pygame.draw.rect(surf, YELLOW if selected else GRAY, r, 2, border_radius=5)
        draw_text(surf, f, key_label, (r.x + 5, r.y + 2), GRAY)
        icon = _slot_icon(surf, r, ("spear", "bow")[int(key_label) - 1], owned=weapon is not None)
        if weapon:
            text = weapon.label()
        else:
            text = "없음" if icon else f"{name} (없음)"   # 아이콘이 있으면 짧게
        draw_text(surf, f, text, (r.centerx + (16 if icon else 0), r.centery),
                  WHITE if weapon else GRAY, center=True)
        x += 100
    r = pygame.Rect(x, 10, 92, 40)
    pygame.draw.rect(surf, (50, 50, 60), r, border_radius=5)
    pygame.draw.rect(surf, GRAY, r, 2, border_radius=5)
    draw_text(surf, f, "3", (r.x + 5, r.y + 2), GRAY)
    icon = _slot_icon(surf, r, "potion", owned=inv.potions > 0)
    draw_text(surf, f, f"물약 x{inv.potions}" if not icon else f"x{inv.potions}",
              (r.centerx + (16 if icon else 0), r.centery), RED if inv.potions else GRAY, center=True)

    # 키 4칸 (건물별)
    draw_text(surf, f, "키", (260, 64))
    for i, (zid, name) in enumerate(ZONE_NAMES.items()):
        r = pygame.Rect(282 + i * 88, 60, 84, 26)
        got = inv.has_key_for(zid)
        pygame.draw.rect(surf, (70, 58, 20) if got else (40, 40, 48), r, border_radius=4)
        pygame.draw.rect(surf, GOLD if got else GRAY, r, 1, border_radius=4)
        draw_text(surf, game.font_tiny, name, r.center, GOLD if got else GRAY, center=True)

    # 전체 지도
    draw_minimap(surf, pygame.Rect(SCREEN_W - 120, 8, 108, 80), current_zone_id, game.is_night)


def draw_message(surf, game, y):
    if game.message_timer <= 0 or not game.message:
        return
    img = game.font.render(game.message, True, WHITE)
    rect = img.get_rect(center=(SCREEN_W // 2, y))
    bg = rect.inflate(24, 10)
    shade = pygame.Surface(bg.size, pygame.SRCALPHA)
    shade.fill((0, 0, 0, 170))
    surf.blit(shade, bg)
    surf.blit(img, rect)
