"""상단 HUD(목숨, 체력, 인벤토리, 낮/밤, 전체 지도)와 공용 그리기 함수."""
import pygame

from themes import load_sprite

from settings import (SCREEN_W, HUD_HEIGHT, ZONE_LAYOUT, PLAYER_MAX_HP, FINAL_ZONE_ID,
                      ZONE_NAMES, BOSS_NAME, ITEM_SPRITES,
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


def draw_hud(surf, game, current_zone_id=None):
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
