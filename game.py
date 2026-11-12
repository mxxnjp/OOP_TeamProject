"""Game: 메인 루프, 전역 상태(플레이어, 월드, 낮/밤, 키), 화면 전환을 관리."""
import os

# 화면을 확대할 때 계단 현상 대신 부드럽게 보간 (창을 만들기 전에 설정해야 적용됨)
os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "linear")

import pygame

from settings import (SCREEN_W, SCREEN_H, FPS, TITLE, FONT_NAMES, PLAYER_LIVES, ZONE_COUNT,
                      DAY_DURATIONS, CENTER_NAME, FINAL_ZONE_NAME, BOSS_NAME, KEY_ORDINALS,
                      PURPLE, RED, YELLOW)
from world import World
from entities import Player, Boss
from items import Key
from scenes import (CenterScene, ZoneScene, TransitionScene, EndScene, PauseScene,
                    GraduationScene)


class Game:
    def __init__(self, seed=None):
        pygame.init()
        pygame.display.set_caption(TITLE)
        # SCALED: 800x640 해상도는 그대로 두고 창/모니터 크기에 맞게 확대 (마우스 좌표도 자동 보정)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED)
        self.clock = pygame.time.Clock()
        self.font_tiny = pygame.font.SysFont(FONT_NAMES, 11, bold=True)
        self.font_small = pygame.font.SysFont(FONT_NAMES, 15)
        self.font = pygame.font.SysFont(FONT_NAMES, 20)
        self.font_big = pygame.font.SysFont(FONT_NAMES, 40, bold=True)
        self.seed = seed
        self.max_lives = PLAYER_LIVES
        self.running = True
        self.reset()

    # ---------------- 상태 초기화 ----------------
    def reset(self):
        """목숨 3개를 다 잃거나 '처음부터 다시'를 고르면 전부 초기화."""
        self.world = World(self.seed)
        self.player = Player()
        self.day = 1
        self.is_night = False
        self.day_timer = self.day_duration()
        self.message = ""
        self.message_timer = 0.0
        self.world.start_day()
        self.scene = TransitionScene(
            self, [TITLE, f"{CENTER_NAME}에서 눈을 떴다...",
                   f"낮({self.day_timer}초) 동안 건물을 돌며 무기를 모으자"],
            on_finish=self.return_to_center)

    def change_scene(self, scene):
        self.scene = scene

    def notify(self, text, duration=2.5):
        if text:
            self.message = text
            self.message_timer = duration

    @property
    def all_keys_collected(self):
        return self.player.inventory.key_count >= ZONE_COUNT

    # ---------------- 화면 이동 ----------------
    def enter_zone(self, zone_id):
        zone = self.world.zones[zone_id]
        self.player.x, self.player.y = zone.entrance
        self.change_scene(ZoneScene(self, zone))
        self.notify(f"{zone.name}에 들어왔다.")

    def return_to_center(self):
        self.change_scene(CenterScene(self))

    def enter_final_stage(self):
        final = self.world.final
        final.reset_encounter()

        def go():
            self.player.x, self.player.y = final.entrance
            self.change_scene(ZoneScene(self, final))

        self.change_scene(TransitionScene(
            self, [FINAL_ZONE_NAME, f"{BOSS_NAME}이(가) 최종 탈출구를 막고 있다", "쓰러뜨리고 졸업하자!"],
            on_finish=go, color=PURPLE))

    # ---------------- 낮 / 밤 ----------------
    def day_duration(self):
        """오늘 낮의 제한 시간. 날이 갈수록 짧아지고, 표의 마지막 값에서 멈춘다."""
        return DAY_DURATIONS[min(self.day, len(DAY_DURATIONS)) - 1]

    def update_clock(self, dt):
        if not self.is_night:
            self.day_timer -= dt
            if self.day_timer <= 0:
                self.start_night()

    def start_night(self):
        """낮 시간이 끝나면 '그 자리에서' 바로 밤. 안내 화면 후 하던 화면으로 돌아간다."""
        self.is_night = True
        here = self.scene
        zone = here.zone if isinstance(here, ZoneScene) else None
        cleared = {k.zone_id for k in self.player.inventory.keys}
        self.world.start_night(cleared, player_zone=zone, player_pos=(self.player.x, self.player.y))
        if self.all_keys_collected:
            lines = ["밤이 찾아왔다...", f"키는 모두 모았다. {FINAL_ZONE_NAME}으로 가자"]
        else:
            lines = ["밤이 찾아왔다...", "건물마다 괴물이 깨어났다",
                     "아무 건물에서나 한 마리를 쓰러뜨리면 아침이 온다"]
        self.change_scene(TransitionScene(self, lines, on_finish=lambda: self.change_scene(here),
                                          color=PURPLE))

    def start_day(self, message=None):
        self.is_night = False
        self.day += 1
        self.day_timer = self.day_duration()
        self.world.start_day()
        self.notify(message or "아침이 밝았다. 괴물이 사라졌다.", 3.5)

    def on_monster_killed(self, zone, monster):
        if isinstance(monster, Boss):
            zone.exit_open = True
            self.notify(f"{BOSS_NAME}을(를) 쓰러뜨렸다! 최종 탈출구가 열렸다!", 4)
            return
        count = self.player.inventory.add_key(Key(zone.id))
        if count < ZONE_COUNT:
            self.start_day(f"{KEY_ORDINALS[count - 1]} 키를 획득하였습니다! 아침이 밝았다.")
        else:
            # 마지막 키: 낮으로 바뀌지 않고, 이 건물에 탈출로가 생긴다
            self.world.clear_monsters()
            zone.exit_open = True
            self.notify("모든 구역 키를 획득하였습니다. 탈출구가 나타났다!", 4)

    # ---------------- 사망 / 승리 ----------------
    def on_player_death(self, zone=None):
        self.player.lives -= 1
        if self.player.lives <= 0:
            self.change_scene(EndScene(self, "GAME OVER", "목숨을 모두 잃었다... 처음부터 다시.", RED))
            return
        self.player.respawn()
        self.return_to_center()
        if zone is not None and zone.is_final:
            # 보스전 실패: 키는 유지한 채 중앙으로, 다시 낮부터 무기 파밍
            self.start_day(f"{BOSS_NAME}에게 졌다... 무기를 모아 EXIT로 다시 도전하자. (남은 목숨 {self.player.lives})")
        else:
            self.notify(f"쓰러졌다! {CENTER_NAME}에서 다시 깨어났다. (남은 목숨 {self.player.lives})", 3.5)

    def graduate(self):
        self.change_scene(GraduationScene(self))

    def finish(self, choice):
        if choice == "grad":
            self.change_scene(EndScene(self, "대학원 입학", "...졸업은 끝이 아니었다.", YELLOW,
                                       note="HUFS RUN 시즌2: 대학원 편 - Coming soon"))
        else:
            self.change_scene(EndScene(self, "취업 성공!", "...하지만 회사도 미로였다.", YELLOW,
                                       note="HUFS RUN 시즌2: 회사 탈출 편 - Coming soon"))

    def toggle_fullscreen(self):
        """F11: 어느 화면에서든 전체화면 <-> 창 모드. 지원 안 되는 환경이면 메시지만 띄움."""
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            self.notify("이 환경에서는 전체화면을 지원하지 않습니다.")

    # ---------------- 메인 루프 ----------------
    def step(self, dt, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                  and self.scene.pausable):
                self.change_scene(PauseScene(self, self.scene))
            else:
                self.scene.handle_event(event)
        scene = self.scene
        scene.update(dt)
        if scene.advances_clock and self.scene is scene:
            self.update_clock(dt)
        self.message_timer = max(0.0, self.message_timer - dt)
        self.scene.draw(self.screen)

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)
            self.step(dt, pygame.event.get())
            pygame.display.flip()
        pygame.quit()
