"""화면(Scene) 단위 상태 관리. 모든 Scene은 handle_event / update / draw를 구현한다."""
import pygame

from settings import (SCREEN_W, SCREEN_H, HUD_HEIGHT, TILE, ZONE_LAYOUT, MAZE_COLS, MAZE_ROWS,
                      TRANSITION_TIME, NIGHT_VISION_RADIUS, CENTER_REGEN_PER_SEC,
                      BG, BLACK, WHITE, GRAY, YELLOW, GOLD, GREEN, RED, PURPLE, HOME_COLOR, DOOR_COLOR)
from hud import draw_hud, draw_message, draw_text

MOVE_KEYS = {
    pygame.K_w: (0, -1), pygame.K_UP: (0, -1),
    pygame.K_s: (0, 1), pygame.K_DOWN: (0, 1),
    pygame.K_a: (-1, 0), pygame.K_LEFT: (-1, 0),
    pygame.K_d: (1, 0), pygame.K_RIGHT: (1, 0),
}
RIGHT_CLICK = 3


class Scene:
    advances_clock = True   # True면 이 화면에 있는 동안 밤 타이머가 흐른다

    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


# =====================================================================
# 중앙(집): 전체 지도 화면. 안전지대 + 체력 회복. 구역을 우클릭하면 입장
# =====================================================================
class CenterScene(Scene):
    MINI_SCALE = 10

    def __init__(self, game):
        super().__init__(game)
        self.regen_acc = 0.0
        w, h = MAZE_COLS * self.MINI_SCALE, MAZE_ROWS * self.MINI_SCALE
        margin_x, margin_y = 80, 50
        self.zone_rects = {}
        for zid, (lx, ly) in ZONE_LAYOUT.items():
            x = margin_x if lx == 0 else SCREEN_W - margin_x - w
            y = HUD_HEIGHT + margin_y if ly == 0 else SCREEN_H - margin_y - h
            self.zone_rects[zid] = pygame.Rect(x, y, w, h)
        self.home_pos = (SCREEN_W // 2, HUD_HEIGHT + (SCREEN_H - HUD_HEIGHT) // 2)

    def handle_event(self, event):
        g = self.game
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == RIGHT_CLICK:
            for zid, rect in self.zone_rects.items():
                if rect.collidepoint(event.pos):
                    g.enter_zone(zid)
                    return
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n and not g.is_night:
                g.start_night()
            elif event.key == pygame.K_3:
                g.notify(g.player.drink_potion())

    def update(self, dt):
        p = self.game.player
        self.regen_acc += dt * CENTER_REGEN_PER_SEC
        if self.regen_acc >= 1:
            p.heal(int(self.regen_acc))
            self.regen_acc %= 1

    def draw(self, surf):
        g = self.game
        surf.fill((20, 26, 22))
        s = self.MINI_SCALE
        mouse = pygame.mouse.get_pos()
        for zid, rect in self.zone_rects.items():
            zone = g.world.zones[zid]
            # 집에서 각 구역 입구로 이어지는 통로
            ex, ey = zone.entrance
            pygame.draw.line(surf, HOME_COLOR, self.home_pos,
                             (rect.x + ex * s + s // 2, rect.y + ey * s + s // 2), 6)
        for zid, rect in self.zone_rects.items():
            zone = g.world.zones[zid]
            surf.blit(zone.surface(s), rect)
            dx, dy = zone.exit_door
            pygame.draw.rect(surf, DOOR_COLOR, (rect.x + dx * s, rect.y + dy * s, s, s))
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(surf, YELLOW if hover else GRAY, rect, 3 if hover else 1)
            label = f"{zid}구역" + (" - 괴물 출몰" if g.is_night and zone.monsters else "")
            draw_text(surf, g.font_small, label, (rect.x, rect.y - 22), PURPLE if g.is_night else WHITE)

        pygame.draw.circle(surf, HOME_COLOR, self.home_pos, 58)
        pygame.draw.circle(surf, WHITE, self.home_pos, 58, 2)
        draw_text(surf, g.font, "중앙 (집)", (self.home_pos[0], self.home_pos[1] - 12), WHITE, center=True)
        draw_text(surf, g.font_small, "안전지대 · 회복", (self.home_pos[0], self.home_pos[1] + 14),
                  WHITE, center=True)

        hint = "구역 우클릭: 입장    3: 물약"
        hint += "    N: 밤 시작(파밍 끝)" if not g.is_night else "    괴물을 처치해 열쇠를 얻자"
        draw_text(surf, g.font_small, hint, (SCREEN_W // 2, SCREEN_H - 18), GRAY, center=True)

        draw_hud(surf, g, current_zone_id=None)
        draw_message(surf, g, SCREEN_H - 50)


# =====================================================================
# 구역(서브 미로) 화면: 탐험, 파밍, 전투, 탈출
# =====================================================================
class ZoneScene(Scene):
    def __init__(self, game, zone):
        super().__init__(game)
        self.zone = zone
        self.dark = pygame.Surface((SCREEN_W, SCREEN_H - HUD_HEIGHT), pygame.SRCALPHA)

    @staticmethod
    def to_world(screen_pos):
        """화면 좌표 -> 미로(월드) 좌표 (HUD 높이만큼 보정)."""
        return screen_pos[0], screen_pos[1] - HUD_HEIGHT

    def handle_event(self, event):
        g, p = self.game, self.game.player
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == RIGHT_CLICK:
            g.notify(p.attack(self.to_world(event.pos), self.zone))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                g.notify(p.inventory.cycle())
            elif event.key in (pygame.K_1, pygame.K_2):
                g.notify(p.inventory.select_slot(event.key - pygame.K_1))
            elif event.key == pygame.K_3:
                g.notify(p.drink_potion())

    def update(self, dt):
        g, p, zone = self.game, self.game.player, self.zone
        p.update(dt)

        pressed = pygame.key.get_pressed()
        for key, (dx, dy) in MOVE_KEYS.items():
            if pressed[key]:
                if p.try_move(dx, dy, zone):
                    self.on_player_moved()
                    if g.scene is not self:   # 이동으로 화면이 바뀌었으면 중단
                        return
                break

        zone.update(dt, p, g)
        if not p.alive:
            g.on_player_death()

    def on_player_moved(self):
        g, p, zone = self.game, self.game.player, self.zone
        pos = (p.x, p.y)
        zone.collect_pickups(p, g)
        if pos == zone.entrance:
            g.return_to_center()
        elif pos == zone.exit_door:
            key = p.inventory.key
            if key is None:
                g.notify("탈출구다! 하지만 열쇠가 필요하다.")
            elif key.zone_id != zone.id:
                g.notify(f"열리지 않는다... 이 열쇠는 {key.zone_id}구역용이다.")
            else:
                g.win()

    def draw(self, surf):
        g, p, zone = self.game, self.game.player, self.zone
        surf.fill(BG)
        surf.blit(zone.surface(), (0, HUD_HEIGHT))

        # 입구(집으로) / 탈출구
        ex, ey = zone.entrance
        r = pygame.Rect(ex * TILE, HUD_HEIGHT + ey * TILE, TILE, TILE)
        pygame.draw.rect(surf, HOME_COLOR, r)
        draw_text(surf, g.font_small, "H", r.center, WHITE, center=True)
        dx, dy = zone.exit_door
        r = pygame.Rect(dx * TILE, HUD_HEIGHT + dy * TILE, TILE, TILE)
        key = p.inventory.key
        door_color = GREEN if key and key.zone_id == zone.id else DOOR_COLOR
        pygame.draw.rect(surf, door_color, r)
        pygame.draw.rect(surf, GOLD, r, 2)
        draw_text(surf, g.font_tiny, "EXIT", r.center, WHITE, center=True)

        for item in zone.pickups:
            item.draw(surf, g.font_small)
        for m in zone.monsters:
            m.draw(surf)
        for proj in zone.projectiles:
            proj.draw(surf)
        p.draw(surf)

        if g.is_night:
            self._draw_darkness(surf)

        draw_hud(surf, g, current_zone_id=zone.id)
        draw_text(surf, g.font_small, f"{zone.id}구역", (8, HUD_HEIGHT + 4), WHITE)
        draw_message(surf, g, SCREEN_H - 24)

    def _draw_darkness(self, surf):
        cx, cy = self.game.player.world_center()
        base = NIGHT_VISION_RADIUS * TILE
        self.dark.fill((0, 0, 15, 225))
        for scale, alpha in ((1.35, 170), (1.15, 100), (1.0, 0)):
            pygame.draw.circle(self.dark, (0, 0, 15, alpha), (cx, cy), base * scale)
        surf.blit(self.dark, (0, HUD_HEIGHT))


# =====================================================================
# 안내 화면 (밤이 찾아왔다 등). 아무 키나 누르면 스킵
# =====================================================================
class TransitionScene(Scene):
    advances_clock = False

    def __init__(self, game, lines, on_finish, color=WHITE):
        super().__init__(game)
        self.lines = lines
        self.on_finish = on_finish
        self.color = color
        self.timer = 0.0
        self.done = False

    def _finish(self):
        if not self.done:
            self.done = True
            self.on_finish()

    def handle_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._finish()

    def update(self, dt):
        self.timer += dt
        if self.timer >= TRANSITION_TIME:
            self._finish()

    def draw(self, surf):
        surf.fill(BLACK)
        alpha = min(1.0, self.timer / 0.6)
        color = tuple(int(c * alpha) for c in self.color)
        y = SCREEN_H // 2 - (len(self.lines) - 1) * 24
        for i, line in enumerate(self.lines):
            font = self.game.font_big if i == 0 else self.game.font
            draw_text(surf, font, line, (SCREEN_W // 2, y + i * 48), color, center=True)
        draw_text(surf, self.game.font_small, "아무 키나 눌러 건너뛰기", (SCREEN_W // 2, SCREEN_H - 30),
                  GRAY, center=True)




# =====================================================================
# 게임 종료 화면 (탈출 성공 / 게임 오버)
# =====================================================================
class EndScene(Scene):
    advances_clock = False

    def __init__(self, game, title, subtitle, color):
        super().__init__(game)
        self.title, self.subtitle, self.color = title, subtitle, color

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.reset()
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

    def draw(self, surf):
        surf.fill(BLACK)
        g = self.game
        draw_text(surf, g.font_big, self.title, (SCREEN_W // 2, SCREEN_H // 2 - 40), self.color, center=True)
        draw_text(surf, g.font, self.subtitle, (SCREEN_W // 2, SCREEN_H // 2 + 10), WHITE, center=True)
        draw_text(surf, g.font_small, "R: 처음부터 다시    ESC: 종료", (SCREEN_W // 2, SCREEN_H // 2 + 60),
                  GRAY, center=True)
