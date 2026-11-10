"""Game: 메인 루프, 전역 상태(플레이어, 월드, 낮/밤), 화면 전환을 관리."""
import pygame

from settings import (SCREEN_W, SCREEN_H, FPS, TITLE, FONT_NAMES, PLAYER_LIVES,
                      NIGHT_DURATION, PURPLE, GREEN, RED, WHITE)
from world import World
from entities import Player
from scenes import CenterScene, ZoneScene, TransitionScene, EndScene, PauseScene


class Game:
    def __init__(self, seed=None):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
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
        """목숨 3개를 다 잃거나 R을 누르면 전부 처음부터."""
        self.world = World(self.seed)
        self.player = Player()
        self.day = 1
        self.is_night = False
        self.night_timer = 0.0
        self.message = ""
        self.message_timer = 0.0
        self.world.start_day()
        self.scene = TransitionScene(
            self, ["미로 한가운데에 떨어졌다...", "낮 동안 미로를 탐험해 무기를 모으자"],
            on_finish=self.return_to_center)

    def change_scene(self, scene):
        self.scene = scene

    def notify(self, text, duration=2.5):
        if text:
            self.message = text
            self.message_timer = duration

    # ---------------- 화면 이동 ----------------
    def enter_zone(self, zone_id):
        zone = self.world.zones[zone_id]
        self.player.x, self.player.y = zone.entrance
        self.change_scene(ZoneScene(self, zone))
        self.notify(f"{zone_id}구역에 들어왔다.")

    def return_to_center(self):
        self.change_scene(CenterScene(self))

    # ---------------- 낮 / 밤 ----------------
    def start_night(self):
        self.change_scene(TransitionScene(
            self, ["밤이 찾아왔다...", "미로가 움직이고, 괴물이 깨어난다", "중앙은 안전하다"],
            on_finish=self._begin_night, color=PURPLE))

    def _begin_night(self):
        self.is_night = True
        self.night_timer = NIGHT_DURATION
        self.world.start_night()
        self.return_to_center()

    def end_night(self):
        self.is_night = False
        self.day += 1
        self.world.start_day()
        self.notify("아침이 밝았다. 괴물이 사라졌다.")

    def update_clock(self, dt):
        if self.is_night:
            self.night_timer -= dt
            if self.night_timer <= 0:
                self.end_night()

    # ---------------- 사망 / 승리 ----------------
    def on_player_death(self):
        self.player.lives -= 1
        if self.player.lives <= 0:
            self.change_scene(EndScene(self, "GAME OVER", "목숨을 모두 잃었다.", RED))
            return
        self.player.respawn()
        self.return_to_center()
        self.notify(f"쓰러졌다! 중앙에서 다시 깨어났다. (남은 목숨 {self.player.lives})", 3.5)

    def win(self):
        self.change_scene(EndScene(self, "탈출 성공!", f"{self.day}일 만에 미로를 빠져나왔다.", GREEN))

    # ---------------- 메인 루프 ----------------
    def step(self, dt, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
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
