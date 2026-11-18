"""화면(Scene) 단위 상태 관리. 모든 Scene은 handle_event / update / draw를 구현한다."""
import pygame

from settings import (SCREEN_W, SCREEN_H, HUD_HEIGHT, TILE, ZONE_LAYOUT, VIEW_COLS, VIEW_ROWS,
                      TRANSITION_TIME, NIGHT_VISION_RADIUS, CENTER_REGEN_PER_SEC,
                      ZONE_BUILDING_IMAGES, CENTER_IMAGE, CENTER_MAP_CROPS, CENTER_BUILDING_ADJUST, CENTER_NIGHT_SHADE,
                      CENTER_ROOM_IMAGE, CENTER_LABEL,
                      CENTER_NAME, FINAL_ZONE_NAME,
                      BG, BLACK, WHITE, GRAY, YELLOW, GOLD, GREEN, PURPLE, HOME_COLOR, DOOR_COLOR)
from buttons import ZoomButton
from hud import draw_hud, draw_message, draw_text, hud_skin, center_map_skin, screen_background
from themes import load_image, load_sprite
from settings import PLAYER_CHARACTERS, TITLE as TITLE_TEXT

MOVE_KEYS = {
    pygame.K_w: (0, -1), pygame.K_UP: (0, -1),
    pygame.K_s: (0, 1), pygame.K_DOWN: (0, 1),
    pygame.K_a: (-1, 0), pygame.K_LEFT: (-1, 0),
    pygame.K_d: (1, 0), pygame.K_RIGHT: (1, 0),
}
LEFT_CLICK, RIGHT_CLICK = 1, 3
ATTACK_KEYS = (pygame.K_SPACE,)   # 마우스 없이 공격: 바라보는 방향으로


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
    CENTER_BOX = (160, 108)  # 가운데 과방 그림 최대 크기(px)

    def __init__(self, game):
        super().__init__(game)
        self.regen_acc = 0.0
        w, h = VIEW_COLS * self.MINI_SCALE, VIEW_ROWS * self.MINI_SCALE
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

        # 가운데 과방 그림 (없으면 파란 원)
        self.center_img = None
        img = load_image(CENTER_IMAGE)
        if img:
            k = min(self.CENTER_BOX[0] / img.get_width(), self.CENTER_BOX[1] / img.get_height())
            self.center_img = pygame.transform.smoothscale(img, (int(img.get_width() * k),
                                                                 int(img.get_height() * k)))

        # 과방 지도 디자인 그림이 있으면: 배경·건물·과방을 그 그림에서 잘라 그림 속 위치 그대로 배치
        self.skin = center_map_skin() if center_map_skin().load() else None
        self.background = None
        if self.skin:
            sk = self.skin
            self.background = sk.background()
            play = pygame.Rect(0, HUD_HEIGHT, SCREEN_W, SCREEN_H - HUD_HEIGHT)
            for zid, crop in CENTER_MAP_CROPS.items():
                art = load_image(ZONE_BUILDING_IMAGES.get(zid))
                size, dx, dy = CENTER_BUILDING_ADJUST.get(zid, (1.0, 0, 0))   # 건물별 크기·위치 미세 조정
                if art:     # 건물 그림이 있으면 그 그림을 디자인 그림 속 자리에 (밤 색감으로)
                    img = sk.building(art, crop, sk.tone_of(crop), fit=1.08 * size)   # 같은 건물 색감으로
                else:       # 없으면 디자인 그림에서 잘라낸 건물
                    img = sk.piece(crop, sk.BUILDING_SCALE * size)
                self.building_imgs[zid] = img
                cx, cy = sk.center_point(crop)
                self.zone_rects[zid] = img.get_rect(center=(cx + dx, cy + dy)).clamp(play)
            self.home_pos = tuple(map(int, sk.center_point(sk.CENTER)))
            room = load_image(CENTER_ROOM_IMAGE)
            self.center_labels = []
            if room:        # 과방 그림 + 이름표 2개(위: 과방 이름, 아래: 안전지대·회복)
                self.center_img = sk.building(room, sk.CENTER, sk.tone_of(sk.CENTER), fit=1.08,
                                              feather=6, scale=sk.CENTER_SCALE)
                r = self.center_img.get_rect(center=self.home_pos)
                top = sk.label(game.font_small.render(CENTER_LABEL, True, (235, 230, 245)))
                bottom = sk.label(game.font_small.render("+  안전지대 · 회복", True, (235, 230, 245)))
                self.center_labels = [(top, top.get_rect(center=(r.centerx, r.top + 4))),
                                      (bottom, bottom.get_rect(center=(r.centerx, r.bottom - 4)))]
            else:           # 없으면 디자인 그림의 과방 조각 (이름표 포함)
                self.center_img = sk.piece(sk.CENTER, sk.CENTER_SCALE)

        # 건물 그림 = 9강 버튼(ZoomButton). 마우스를 올리면 커지고, 눌렀다 떼면 그 건물로 입장(콜백)
        play_area = pygame.Rect(0, HUD_HEIGHT, SCREEN_W, SCREEN_H - HUD_HEIGHT)
        self.buttons = {zid: ZoomButton(game.screen, self.zone_rects[zid].topleft, img,
                                        callBack=lambda z=zid: game.enter_zone(z), bounds=play_area)
                        for zid, img in self.building_imgs.items()}

    def handle_event(self, event):
        g = self.game
        for button in self.buttons.values():      # 강의처럼 이벤트를 버튼에 넘겨 줌
            if button.handleEvent(event):
                return                            # 클릭됨 -> 콜백으로 이미 건물에 들어감
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (LEFT_CLICK, RIGHT_CLICK):
            for zid, rect in self.zone_rects.items():   # 그림이 없는 건물(미로 미리보기)용
                if zid not in self.buttons and rect.collidepoint(event.pos):
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
        full_bg = screen_background()
        if full_bg:                          # 메인 배경 그림 (HUD 뒤까지 화면 전체)
            surf.blit(full_bg, (0, 0))
        elif self.background:                # 없으면 디자인 그림을 흐리게
            surf.blit(self.background, (0, HUD_HEIGHT))
        s = self.MINI_SCALE
        mouse = pygame.mouse.get_pos()
        tags = []                            # 이름표: 맨 나중에(밤 어둠 위에) 그림
        for zid, rect in self.zone_rects.items():
            zone = g.world.zones[zid]
            # 과방에서 각 건물로 이어지는 길
            if zid in self.building_imgs:
                target = rect.midbottom if ZONE_LAYOUT[zid][1] == 0 else rect.midtop
            else:
                ex, ey = zone.entrance
                target = (rect.x + ex * s + s // 2, rect.y + ey * s + s // 2)
            if self.skin:                    # 디자인 그림처럼 가는 보라빛 길
                pygame.draw.line(surf, (120, 105, 160), self.home_pos, target, 4)
                pygame.draw.line(surf, (175, 160, 215), self.home_pos, target, 2)
            else:
                pygame.draw.line(surf, HOME_COLOR, self.home_pos, target, 6)

        # 가운데 과방 (건물보다 먼저 그려서, 커진 건물 그림이 위로 오게)
        if self.center_img:
            r = self.center_img.get_rect(center=self.home_pos)
            surf.blit(self.center_img, r)
            tags.extend(getattr(self, "center_labels", []))   # 이름표는 밤 어둠 위에 (밝게 보이게)
        if self.center_img and not self.skin:            # 디자인 그림에는 이름표가 이미 있음
            r = self.center_img.get_rect(center=self.home_pos)
            text = "안전지대 · 회복"
            img = g.font_tiny.render(text, True, WHITE)
            tag = img.get_rect(midtop=(r.centerx, r.bottom - 2))
            pygame.draw.rect(surf, (20, 26, 22), tag.inflate(10, 4), border_radius=4)
            surf.blit(img, tag)
        elif not self.center_img:
            pygame.draw.circle(surf, HOME_COLOR, self.home_pos, 58)
            pygame.draw.circle(surf, WHITE, self.home_pos, 58, 2)
            draw_text(surf, g.font_small, CENTER_NAME, (self.home_pos[0], self.home_pos[1] - 12), WHITE,
                      center=True)
            draw_text(surf, g.font_small, "안전지대 · 회복", (self.home_pos[0], self.home_pos[1] + 14),
                      WHITE, center=True)

        # 마우스가 올라간(커진) 건물은 다른 건물 위에 보이도록 맨 나중에 그림
        hovered = [z for z, b in self.buttons.items() if b.state != b.STATE_NORMAL]
        order = [z for z in self.zone_rects if z not in hovered] + hovered
        for zid in order:
            rect = self.zone_rects[zid]
            zone = g.world.zones[zid]
            if zid in self.buttons:
                button = self.buttons[zid]
                button.draw(surf)                       # 상태(기본/hover/누름)에 맞는 그림
                rect = button.draw_rect()               # 이름·EXIT 표시도 커진 그림에 맞춤
                if zone.exit_open:
                    draw_text(surf, g.font_tiny, " EXIT ", (rect.right - 24, rect.top + 10), GREEN, center=True)
            else:
                hover = rect.collidepoint(mouse)
                surf.blit(zone.surface(s), rect)
                if zone.exit_open:
                    dx, dy = zone.exit_door
                    pygame.draw.rect(surf, GREEN, (rect.x + dx * s, rect.y + dy * s, s, s))
                pygame.draw.rect(surf, YELLOW if hover else GRAY, rect, 3 if hover else 1)
            label = f"{zid}. {zone.name}"
            if inv.has_key_for(zid):
                label += " - 키 획득"
            if self.skin:                    # 디자인 그림의 이름표 틀 + 실제 상태 글자, 건물 위 가운데
                color = GOLD if inv.has_key_for(zid) else ((205, 175, 255) if g.is_night else (235, 230, 245))
                tag_img = self.skin.label(g.font.render(label, True, color))
                tag = tag_img.get_rect(midbottom=(rect.centerx, rect.top + 2))
                center = self.center_img.get_rect(center=self.home_pos)
                for _, label_rect in getattr(self, "center_labels", []):
                    center = center.union(label_rect)
                center = center.inflate(16, 0)
                if tag.colliderect(center):              # 가운데 과방과 겹치면 바깥쪽으로 밀기
                    if ZONE_LAYOUT[zid][0] == 0:
                        tag.right = center.left
                    else:
                        tag.left = center.right
                tag.clamp_ip(pygame.Rect(0, HUD_HEIGHT + 2, SCREEN_W, SCREEN_H))
                tags.append((tag_img, tag))
                continue
            color = GOLD if inv.has_key_for(zid) else (PURPLE if g.is_night else WHITE)
            img = g.font_small.render(label, True, color)
            if ZONE_LAYOUT[zid][0] == 0:       # 왼쪽 건물: 이름을 왼쪽 정렬
                tag = img.get_rect(bottomleft=(rect.x, rect.y - 4))
            else:                              # 오른쪽 건물: 가운데 과방과 안 겹치게 오른쪽 정렬
                tag = img.get_rect(bottomright=(rect.right, rect.y - 4))
            tag.top = max(tag.top, HUD_HEIGHT + 2)
            tags.append((img, tag))

        if g.is_night:                       # 밤: 지도(HUD 아래)를 조금 어둡게
            if not hasattr(self, "_night_shade"):
                self._night_shade = pygame.Surface((SCREEN_W, SCREEN_H - HUD_HEIGHT), pygame.SRCALPHA)
                self._night_shade.fill(CENTER_NIGHT_SHADE)
            surf.blit(self._night_shade, (0, HUD_HEIGHT))
        for img, rect in tags:
            surf.blit(img, rect)

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

    VIEW_W, VIEW_H = SCREEN_W, SCREEN_H - HUD_HEIGHT   # 미로가 보이는 창 크기

    def __init__(self, game, zone):
        super().__init__(game)
        self.zone = zone
        self.dark = pygame.Surface((self.VIEW_W, self.VIEW_H), pygame.SRCALPHA)
        # 미로 전체를 그려 둘 큰 도화지. 위에 HUD 높이만큼 여백을 둬서,
        # 기존 draw() 코드(월드 좌표 + HUD_HEIGHT)를 그대로 쓸 수 있게 한다.
        self.world_w, self.world_h = zone.maze.cols * TILE, zone.maze.rows * TILE
        self.canvas = pygame.Surface((self.world_w, HUD_HEIGHT + self.world_h))
        self.cam = (0, 0)
        self.update_camera()

    @property
    def advances_clock(self):
        return not self.zone.is_final   # 최종 스테이지에서는 낮 타이머가 멈춤

    def update_camera(self):
        """카메라: 플레이어를 화면 가운데에 두되, 미로 바깥이 보이지 않게 가장자리에서 멈춘다."""
        px, py = self.game.player.world_center()
        cx = min(max(0, px - self.VIEW_W / 2), max(0, self.world_w - self.VIEW_W))
        cy = min(max(0, py - self.VIEW_H / 2), max(0, self.world_h - self.VIEW_H))
        self.cam = (int(cx), int(cy))

    def to_world(self, screen_pos):
        """화면 좌표 -> 미로(월드) 좌표 (HUD 높이와 카메라 위치만큼 보정)."""
        return screen_pos[0] + self.cam[0], screen_pos[1] - HUD_HEIGHT + self.cam[1]

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
        self.update_camera()
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
        world = self.canvas                     # 미로 전체를 먼저 큰 도화지에 그리고
        world.blit(zone.surface(), (0, HUD_HEIGHT))

        # 입구(과방으로) / 탈출구
        if not zone.is_final:
            ex, ey = zone.entrance
            r = pygame.Rect(ex * TILE, HUD_HEIGHT + ey * TILE, TILE, TILE)
            pygame.draw.rect(world, HOME_COLOR, r)
            draw_text(world, g.font_small, "H", r.center, WHITE, center=True)
        if zone.exit_open or zone.is_final:   # 일반 건물은 마지막 키를 얻어야 탈출구가 보임
            dx, dy = zone.exit_door
            r = pygame.Rect(dx * TILE, HUD_HEIGHT + dy * TILE, TILE, TILE)
            pygame.draw.rect(world, GREEN if zone.exit_open else DOOR_COLOR, r)
            pygame.draw.rect(world, GOLD, r, 2)
            draw_text(world, g.font_tiny, "EXIT", r.center, WHITE, center=True)

        if zone.items_available(g):             # 밤에는 아이템이 보이지 않음
            for item in zone.pickups:
                item.draw(world, g.font_small)
        for m in zone.monsters:
            m.draw(world, g.font_tiny)
        for proj in zone.projectiles:
            proj.draw(world)
        p.draw(world)

        surf.fill(BG)                           # 카메라가 보는 부분만 화면에 복사
        cx, cy = self.cam
        surf.blit(world, (0, HUD_HEIGHT), pygame.Rect(cx, HUD_HEIGHT + cy, self.VIEW_W, self.VIEW_H))

        if g.is_night or zone.is_final:
            self._draw_darkness(surf)

        draw_hud(surf, g, current_zone_id=zone.id)
        name = g.font_small.render(zone.name, True, WHITE)   # 밝은 배경에서도 보이게 어두운 바탕
        tag = name.get_rect(topleft=(8, HUD_HEIGHT + 4))
        pygame.draw.rect(surf, (20, 20, 28), tag.inflate(8, 2), border_radius=4)
        surf.blit(name, tag)
        draw_message(surf, g, SCREEN_H - 24)

    NIGHT_ALPHA = 228                    # 시야 밖 어두움 (0~255)
    LIGHT_INNER, LIGHT_OUTER = 0.7, 1.6  # 시야 반지름 대비: 이 안은 완전히 밝음 / 이 밖은 완전히 어두움
    _light_cache = {}

    @classmethod
    def light_mask(cls, radius):
        """플레이어 주변 스포트라이트 무늬. 가운데 투명 → 바깥으로 갈수록 부드럽게 어두워짐(smoothstep)."""
        if radius not in cls._light_cache:
            import numpy as np
            r0, r1 = radius * cls.LIGHT_INNER, radius * cls.LIGHT_OUTER
            size = int(r1 * 2) + 2
            yy, xx = np.mgrid[0:size, 0:size]
            d = np.hypot(xx - size / 2, yy - size / 2)
            t = np.clip((d - r0) / (r1 - r0), 0, 1)
            t = t * t * (3 - 2 * t)                       # smoothstep: 경계가 티 나지 않게
            mask = pygame.Surface((size, size), pygame.SRCALPHA)
            mask.fill((0, 0, 15, 0))
            alpha = pygame.surfarray.pixels_alpha(mask)
            alpha[:] = (t * cls.NIGHT_ALPHA).astype(np.uint8).T
            del alpha
            cls._light_cache[radius] = mask
        return cls._light_cache[radius]

    def _draw_darkness(self, surf):
        px, py = self.game.player.world_center()
        cx, cy = px - self.cam[0], py - self.cam[1]      # 화면에서의 플레이어 위치
        self.dark.fill((0, 0, 15, self.NIGHT_ALPHA))
        mask = self.light_mask(int(NIGHT_VISION_RADIUS * TILE))
        # 두 그림 중 더 투명한 쪽을 남김(MIN) → 플레이어 주변만 그라데이션으로 밝아짐
        self.dark.blit(mask, mask.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGBA_MIN)
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
# 캐릭터 선택 (게임 시작할 때): 남학생 / 여학생 앞모습을 보여 주고 고르게 한다
# =====================================================================
class CharacterSelectScene(Scene):
    advances_clock = False
    CARD_W, CARD_H = 240, 320

    def __init__(self, game, on_choose):
        super().__init__(game)
        self.keys = list(PLAYER_CHARACTERS)        # ["boy", "girl"]
        self.selected = 0
        self.on_choose = on_choose                 # 고른 캐릭터 키를 넘겨받아 실행 (콜백)
        self.timer = 0.0

    def card_rect(self, i):
        gap = 60
        total = len(self.keys) * self.CARD_W + (len(self.keys) - 1) * gap
        r = pygame.Rect(0, 0, self.CARD_W, self.CARD_H)
        r.topleft = (SCREEN_W // 2 - total // 2 + i * (self.CARD_W + gap), 190)
        return r

    def choose(self):
        self.on_choose(self.keys[self.selected])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(self.keys)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(self.keys)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.choose()
        elif event.type == pygame.MOUSEMOTION:
            for i in range(len(self.keys)):
                if self.card_rect(i).collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT_CLICK:
            for i in range(len(self.keys)):
                if self.card_rect(i).collidepoint(event.pos):
                    self.selected = i
                    self.choose()
                    return

    def update(self, dt):
        self.timer += dt

    def draw(self, surf):
        g = self.game
        surf.fill((16, 18, 26))
        draw_text(surf, g.font_big, TITLE_TEXT, (SCREEN_W // 2, 80), WHITE, center=True)
        draw_text(surf, g.font, "캐릭터를 선택하세요", (SCREEN_W // 2, 138), GRAY, center=True)
        for i, key in enumerate(self.keys):
            info = PLAYER_CHARACTERS[key]
            r = self.card_rect(i)
            active = i == self.selected
            # 카드 틀(테두리) 없이 캐릭터만. 고른 캐릭터는 발밑 빛 + 살짝 들썩 + 노란 이름
            feet = (r.centerx, r.bottom - 52)
            glow = pygame.Surface((150, 34), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 220, 90, 70) if active else (0, 0, 0, 90), glow.get_rect())
            surf.blit(glow, glow.get_rect(center=feet))
            img = load_sprite(info["sprites"]["down"], 250)          # 앞모습
            bob = 4 if active and int(self.timer * 2) % 2 else 0
            if img:
                if not active:
                    img = img.copy()
                    img.set_alpha(150)                                # 안 고른 쪽은 살짝 흐리게
                surf.blit(img, img.get_rect(midbottom=(feet[0], feet[1] + 6 - bob)))
            else:                                                     # 그림이 아직 없으면 실루엣
                pygame.draw.circle(surf, info["color"], (r.centerx, r.y + 105 - bob), 46)
                pygame.draw.rect(surf, info["color"], (r.centerx - 50, r.y + 160 - bob, 100, 90),
                                 border_radius=24)
            draw_text(surf, g.font, info["name"], (r.centerx, r.bottom - 28),
                      YELLOW if active else WHITE, center=True)
        draw_text(surf, g.font_small, "←→ / 마우스: 고르기    Enter / 클릭: 시작",
                  (SCREEN_W // 2, SCREEN_H - 40), GRAY, center=True)


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

    def _frames(self):
        """HUD 디자인 그림에서 만든 패널·버튼 틀 (그림이 없으면 None → 기본 사각형)."""
        if not hasattr(self, "_frame_cache"):
            skin = hud_skin()
            first, last = self.option_rect(0), self.option_rect(len(self.options) - 1)
            top = SCREEN_H // 2 - 160
            width = max(420, self.game.font_big.size(self.title)[0] + 100,
                        self.game.font.size(self.subtitle)[0] + 100 if self.subtitle else 0)
            self.panel_rect = pygame.Rect(0, 0, width, last.bottom + 70 - top)
            self.panel_rect.midtop = (SCREEN_W // 2, top)
            self._frame_cache = (skin.panel(*self.panel_rect.size), skin.pill(first.width, first.height))
        return self._frame_cache

    def draw(self, surf):
        if self.background:
            self.background.draw(surf)   # 멈춘 게임 화면을 그대로 뒤에 보여줌
            surf.blit(self.shade, (0, HUD_HEIGHT), (0, 0, SCREEN_W, SCREEN_H - HUD_HEIGHT))   # HUD는 밝게 둠
        else:
            surf.fill(BLACK)
        g = self.game
        panel, pill = self._frames()
        if panel:                        # HUD 오른쪽 지도와 같은 덩굴·돌 틀
            surf.blit(panel, self.panel_rect)
        draw_text(surf, g.font_big, self.title, (SCREEN_W // 2, SCREEN_H // 2 - 120), WHITE, center=True)
        if self.subtitle:
            draw_text(surf, g.font, self.subtitle, (SCREEN_W // 2, SCREEN_H // 2 - 72), GRAY, center=True)
        for i, (label, _) in enumerate(self.options):
            rect = self.option_rect(i)
            active = i == self.selected
            if pill:                     # HUD 무기·건물 칸과 같은 알약 모양 버튼
                surf.blit(pill, rect)
                if active:
                    pygame.draw.rect(surf, YELLOW, rect.inflate(2, 2), 2, border_radius=rect.height // 2)
            else:
                pygame.draw.rect(surf, (60, 60, 75) if active else (30, 30, 40), rect, border_radius=8)
                pygame.draw.rect(surf, YELLOW if active else GRAY, rect, 2, border_radius=8)
            draw_text(surf, g.font, label, rect.center, YELLOW if active else WHITE, center=True)
        hint = "↑↓/마우스: 선택   Enter/클릭: 확인"
        if self.on_cancel:
            hint += "   ESC: 계속하기"
        y = (self.panel_rect.bottom + 22) if panel else SCREEN_H // 2 + 175
        draw_text(surf, g.font_small, hint, (SCREEN_W // 2, y), GRAY, center=True)


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
