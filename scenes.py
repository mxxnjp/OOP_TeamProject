"""화면(Scene) 단위 상태 관리. 모든 Scene은 handle_event / update / draw를 구현한다."""
import pygame

from settings import (SCREEN_W, SCREEN_H, HUD_HEIGHT, TILE, ZONE_LAYOUT, MAZE_COLS, MAZE_ROWS,
                      TRANSITION_TIME, NIGHT_VISION_RADIUS, CENTER_REGEN_PER_SEC,
                      ZONE_BUILDING_IMAGES,
                      CENTER_NAME, FINAL_ZONE_NAME,
                      BG, BLACK, WHITE, GRAY, YELLOW, GOLD, GREEN, PURPLE, HOME_COLOR, DOOR_COLOR)
from hud import draw_hud, draw_message, draw_text
from themes import load_image

MOVE_KEYS = {
    pygame.K_w: (0, -1), pygame.K_UP: (0, -1),
    pygame.K_s: (0, 1), pygame.K_DOWN: (0, 1),
    pygame.K_a: (-1, 0), pygame.K_LEFT: (-1, 0),
    pygame.K_d: (1, 0), pygame.K_RIGHT: (1, 0),
}
LEFT_CLICK, RIGHT_CLICK = 1, 3
ATTACK_KEYS = (pygame.K_j,)   # 마우스 없이 공격: 바라보는 방향으로


class Scene:
    advances_clock = True   # True면 이 화면에 있는 동안 낮 타이머가 흐른다
    pausable = False        # True면 ESC로 일시정지 메뉴를 열 수 있다

    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


# =====================================================================
# 중앙(과방): 전체 지도 화면. 안전지대 + 체력 회복. 건물을 클릭하면 입장
# =====================================================================
class CenterScene(Scene):
    pausable = True
    MINI_SCALE = 10
    BUILDING_EXTRA_W = 130   # 건물 그림을 미로 칸보다 얼마나 더 넓게 그릴지(px)

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

        # 건물 그림이 있으면 미로 미리보기 대신 사용 (비율 유지).
        # 그림은 미로 칸보다 가로로 BUILDING_EXTRA_W 만큼 넓은 영역까지 키울 수 있다.
        self.building_imgs = {}
        for zid, rect in self.zone_rects.items():
            img = load_image(ZONE_BUILDING_IMAGES.get(zid))
            if img:
                box = rect.inflate(self.BUILDING_EXTRA_W, 0)
                k = min(box.width / img.get_width(), box.height / img.get_height())
                scaled = pygame.transform.smoothscale(img, (int(img.get_width() * k), int(img.get_height() * k)))
                self.zone_rects[zid] = scaled.get_rect(center=box.center)   # 클릭/테두리도 그림 크기에 맞춤
                self.building_imgs[zid] = scaled

    def handle_event(self, event):
        g = self.game
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (LEFT_CLICK, RIGHT_CLICK):
            for zid, rect in self.zone_rects.items():
                if rect.collidepoint(event.pos):
                    g.enter_zone(zid)
                    return
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_3:
            g.notify(g.player.drink_potion())

    def update(self, dt):
        p = self.game.player
        self.regen_acc += dt * CENTER_REGEN_PER_SEC
        if self.regen_acc >= 1:
            p.heal(int(self.regen_acc))
            self.regen_acc %= 1

    def draw(self, surf):
        g = self.game
        inv = g.player.inventory
        surf.fill((20, 26, 22))
        s = self.MINI_SCALE
        mouse = pygame.mouse.get_pos()
        for zid, rect in self.zone_rects.items():
            zone = g.world.zones[zid]
            # 과방에서 각 건물로 이어지는 길
            if zid in self.building_imgs:
                target = rect.midbottom if ZONE_LAYOUT[zid][1] == 0 else rect.midtop
            else:
                ex, ey = zone.entrance
                target = (rect.x + ex * s + s // 2, rect.y + ey * s + s // 2)
            pygame.draw.line(surf, HOME_COLOR, self.home_pos, target, 6)

        for zid, rect in self.zone_rects.items():
            zone = g.world.zones[zid]
            hover = rect.collidepoint(mouse)
            if zid in self.building_imgs:
                surf.blit(self.building_imgs[zid], rect)
                if hover:
                    pygame.draw.rect(surf, YELLOW, rect.inflate(6, 6), 2, border_radius=4)
                if zone.exit_open:
                    draw_text(surf, g.font_tiny, " EXIT ", (rect.right - 24, rect.top + 10), GREEN, center=True)
            else:
                surf.blit(zone.surface(s), rect)
                if zone.exit_open:
                    dx, dy = zone.exit_door
                    pygame.draw.rect(surf, GREEN, (rect.x + dx * s, rect.y + dy * s, s, s))
                pygame.draw.rect(surf, YELLOW if hover else GRAY, rect, 3 if hover else 1)
            label = f"{zid}. {zone.name}"
            if inv.has_key_for(zid):
                label += "  [키 획득]"
            elif g.is_night and zone.monsters:
                label += f"  - {zone.monster_name} 출몰"
            color = GOLD if inv.has_key_for(zid) else (PURPLE if g.is_night else WHITE)
            draw_text(surf, g.font_small, label, (rect.x, rect.y - 22), color)

        pygame.draw.circle(surf, HOME_COLOR, self.home_pos, 58)
        pygame.draw.circle(surf, WHITE, self.home_pos, 58, 2)
        draw_text(surf, g.font_small, CENTER_NAME, (self.home_pos[0], self.home_pos[1] - 12), WHITE, center=True)
        draw_text(surf, g.font_small, "안전지대 · 회복", (self.home_pos[0], self.home_pos[1] + 14),
                  WHITE, center=True)

        exit_zone = next((z for z in g.world.zones.values() if z.exit_open), None)
        if exit_zone:
            goal = f"{exit_zone.name}의 EXIT로 {FINAL_ZONE_NAME}에 가자"
        elif g.is_night:
            goal = "아무 건물에서나 괴물을 쓰러뜨려 키를 얻자"
        else:
            goal = "밤이 오기 전에 무기를 모으자"
        draw_text(surf, g.font_small, f"건물 클릭: 입장    3: 물약    |    {goal}",
                  (SCREEN_W // 2, SCREEN_H - 18), GRAY, center=True)

        draw_hud(surf, g, current_zone_id=None)
        draw_message(surf, g, SCREEN_H - 50)


# =====================================================================
# 건물(서브 미로) / 최종 스테이지 화면: 탐험, 파밍, 전투, 탈출
# =====================================================================
class ZoneScene(Scene):
    pausable = True

    def __init__(self, game, zone):
        super().__init__(game)
        self.zone = zone
        self.dark = pygame.Surface((SCREEN_W, SCREEN_H - HUD_HEIGHT), pygame.SRCALPHA)

    @property
    def advances_clock(self):
        return not self.zone.is_final   # 최종 스테이지에서는 낮 타이머가 멈춤

    @staticmethod
    def to_world(screen_pos):
        """화면 좌표 -> 미로(월드) 좌표 (HUD 높이만큼 보정)."""
        return screen_pos[0], screen_pos[1] - HUD_HEIGHT

    def facing_target(self):
        """플레이어가 바라보는 방향으로 한 칸 앞 지점 (키보드 공격용 조준점)."""
        p = self.game.player
        cx, cy = p.world_center()
        return cx + p.facing[0] * TILE, cy + p.facing[1] * TILE

    def handle_event(self, event):
        g, p = self.game, self.game.player
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT_CLICK:
            g.notify(p.attack(self.to_world(event.pos), self.zone))      # 마우스 방향으로 공격
        elif event.type == pygame.KEYDOWN:
            if event.key in ATTACK_KEYS:
                g.notify(p.attack(self.facing_target(), self.zone))       # 바라보는 방향으로 공격
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
        if not p.alive and g.scene is self:
            g.on_player_death(zone)

    def on_player_moved(self):
        g, p, zone = self.game, self.game.player, self.zone
        pos = (p.x, p.y)
        zone.collect_pickups(p, g)
        if pos == zone.entrance and not zone.is_final:   # 최종 스테이지는 되돌아갈 수 없음
            g.return_to_center()
        elif pos == zone.exit_door and zone.exit_open:
            if zone.is_final:
                g.graduate()
            else:
                g.enter_final_stage()
        elif pos == zone.exit_door and zone.is_final:
            g.notify("탈출구가 잠겨 있다. 보스를 쓰러뜨려야 열린다.")

    def draw(self, surf):
        g, p, zone = self.game, self.game.player, self.zone
        surf.fill(BG)
        surf.blit(zone.surface(), (0, HUD_HEIGHT))

        # 입구(과방으로) / 탈출구
        if not zone.is_final:
            ex, ey = zone.entrance
            r = pygame.Rect(ex * TILE, HUD_HEIGHT + ey * TILE, TILE, TILE)
            pygame.draw.rect(surf, HOME_COLOR, r)
            draw_text(surf, g.font_small, "H", r.center, WHITE, center=True)
        if zone.exit_open or zone.is_final:   # 일반 건물은 마지막 키를 얻어야 탈출구가 보임
            dx, dy = zone.exit_door
            r = pygame.Rect(dx * TILE, HUD_HEIGHT + dy * TILE, TILE, TILE)
            pygame.draw.rect(surf, GREEN if zone.exit_open else DOOR_COLOR, r)
            pygame.draw.rect(surf, GOLD, r, 2)
            draw_text(surf, g.font_tiny, "EXIT", r.center, WHITE, center=True)

        for item in zone.pickups:
            item.draw(surf, g.font_small)
        for m in zone.monsters:
            m.draw(surf, g.font_tiny)
        for proj in zone.projectiles:
            proj.draw(surf)
        p.draw(surf)

        if g.is_night or zone.is_final:
            self._draw_darkness(surf)

        draw_hud(surf, g, current_zone_id=zone.id)
        draw_text(surf, g.font_small, zone.name, (8, HUD_HEIGHT + 4), WHITE)
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
# 메뉴 화면 공통 부모: 선택지 목록 + 방향키/마우스 선택
# =====================================================================
class MenuScene(Scene):
    advances_clock = False

    def __init__(self, game, title, options, subtitle=None, background=None, on_cancel=None):
        """options: [(글자, 실행할 함수), ...]  background: 뒤에 어둡게 깔 Scene (없으면 검은 화면)"""
        super().__init__(game)
        self.title = title
        self.subtitle = subtitle
        self.options = options
        self.background = background
        self.on_cancel = on_cancel   # ESC를 눌렀을 때 (None이면 ESC 무시)
        self.selected = 0
        self.shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.shade.fill((0, 0, 0, 170))

    def option_rect(self, index):
        rect = pygame.Rect(0, 0, 260, 48)
        rect.center = (SCREEN_W // 2, SCREEN_H // 2 - 10 + index * 62)
        return rect

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.on_cancel:
                self.on_cancel()
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.options[self.selected][1]()
        elif event.type == pygame.MOUSEMOTION:
            for i in range(len(self.options)):
                if self.option_rect(i).collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT_CLICK:
            for i, (_, action) in enumerate(self.options):
                if self.option_rect(i).collidepoint(event.pos):
                    action()
                    return

    def draw(self, surf):
        if self.background:
            self.background.draw(surf)   # 멈춘 게임 화면을 그대로 뒤에 보여줌
            surf.blit(self.shade, (0, 0))
        else:
            surf.fill(BLACK)
        g = self.game
        draw_text(surf, g.font_big, self.title, (SCREEN_W // 2, SCREEN_H // 2 - 120), WHITE, center=True)
        if self.subtitle:
            draw_text(surf, g.font, self.subtitle, (SCREEN_W // 2, SCREEN_H // 2 - 72), GRAY, center=True)
        for i, (label, _) in enumerate(self.options):
            rect = self.option_rect(i)
            active = i == self.selected
            pygame.draw.rect(surf, (60, 60, 75) if active else (30, 30, 40), rect, border_radius=8)
            pygame.draw.rect(surf, YELLOW if active else GRAY, rect, 2, border_radius=8)
            draw_text(surf, g.font, label, rect.center, YELLOW if active else WHITE, center=True)
        hint = "↑↓/마우스: 선택   Enter/클릭: 확인"
        if self.on_cancel:
            hint += "   ESC: 계속하기"
        draw_text(surf, g.font_small, hint, (SCREEN_W // 2, SCREEN_H // 2 + 175), GRAY, center=True)


class PauseScene(MenuScene):
    """ESC 일시정지 메뉴."""

    def __init__(self, game, paused_scene):
        super().__init__(game, "일시정지",
                         [("계속하기", self.resume),
                          ("처음부터 다시", game.reset),
                          ("게임 종료", self.quit)],
                         background=paused_scene, on_cancel=self.resume)
        self.paused_scene = paused_scene

    def resume(self):
        self.game.change_scene(self.paused_scene)

    def quit(self):
        self.game.running = False


class GraduationScene(MenuScene):
    """최종 탈출(졸업) 후 진로 선택: 대학원 vs 취직."""

    def __init__(self, game):
        super().__init__(game, "졸업을 축하합니다!",
                         [("대학원 진학", lambda: game.finish("grad")),
                          ("취업", lambda: game.finish("job"))],
                         subtitle=f"{game.day}일 만에 학교를 탈출했다. 이제 어디로 갈까?")


# =====================================================================
# 게임 종료 화면 (진로 엔딩 / 게임 오버)
# =====================================================================
class EndScene(Scene):
    advances_clock = False

    def __init__(self, game, title, subtitle, color, note=None):
        super().__init__(game)
        self.title, self.subtitle, self.color, self.note = title, subtitle, color, note

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.game.reset()
            elif event.key == pygame.K_ESCAPE:
                self.game.running = False

    def draw(self, surf):
        surf.fill(BLACK)
        g = self.game
        draw_text(surf, g.font_big, self.title, (SCREEN_W // 2, SCREEN_H // 2 - 50), self.color, center=True)
        draw_text(surf, g.font, self.subtitle, (SCREEN_W // 2, SCREEN_H // 2), WHITE, center=True)
        if self.note:
            draw_text(surf, g.font_small, self.note, (SCREEN_W // 2, SCREEN_H // 2 + 40), PURPLE, center=True)
        draw_text(surf, g.font_small, "R: 처음부터 다시    ESC: 종료", (SCREEN_W // 2, SCREEN_H // 2 + 90),
                  GRAY, center=True)
