"""캐릭터: Entity(공통) -> Player(플레이어), Monster(괴물)."""
import math

import pygame

from settings import (TILE, HUD_HEIGHT, PLAYER_MAX_HP, PLAYER_LIVES, PLAYER_MOVE_DELAY,
                      POTION_HEAL_RATIO, MONSTER_MAX_HP, MONSTER_MOVE_DELAY,
                      MONSTER_DETECT_RANGE, MONSTER_MELEE_DAMAGE, MONSTER_MELEE_COOLDOWN,
                      MONSTER_RANGED_COOLDOWN, MONSTER_RANGED_RANGE,
                      BLUE, WHITE, RED, GREEN, MONSTER_COLOR, DARK_RED)
from items import Inventory
from projectiles import PoisonDart

DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Entity:
    """타일 좌표(x, y)와 체력을 가진 모든 캐릭터의 부모 클래스."""

    def __init__(self, x, y, max_hp):
        self.x, self.y = x, y
        self.max_hp = max_hp
        self.hp = max_hp
        self.hurt_timer = 0.0   # 맞았을 때 깜빡임 효과

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        if amount <= 0 or not self.alive:
            return
        self.hp = max(0, self.hp - amount)
        self.hurt_timer = 0.2

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def update_timers(self, dt):
        self.hurt_timer = max(0.0, self.hurt_timer - dt)

    def world_center(self):
        return self.x * TILE + TILE / 2, self.y * TILE + TILE / 2

    def screen_center(self):
        wx, wy = self.world_center()
        return wx, wy + HUD_HEIGHT

    def draw_hp_bar(self, surf):
        cx, cy = self.screen_center()
        w = TILE - 4
        x, y = cx - w / 2, cy - TILE / 2 - 6
        pygame.draw.rect(surf, DARK_RED, (x, y, w, 4))
        pygame.draw.rect(surf, GREEN, (x, y, w * self.hp / self.max_hp, 4))


class Player(Entity):
    def __init__(self):
        super().__init__(0, 0, PLAYER_MAX_HP)
        self.lives = PLAYER_LIVES
        self.inventory = Inventory()
        self.facing = (0, 1)
        self.move_timer = 0.0

    def respawn(self):
        self.hp = self.max_hp
        self.hurt_timer = 0.0

    def update(self, dt):
        self.update_timers(dt)
        self.move_timer = max(0.0, self.move_timer - dt)
        self.inventory.update(dt)

    def try_move(self, dx, dy, zone):
        """한 칸 이동. 성공하면 True."""
        if self.move_timer > 0:
            return False
        self.facing = (dx, dy)
        nx, ny = self.x + dx, self.y + dy
        if zone.maze.is_wall(nx, ny) or zone.monster_at(nx, ny):
            return False
        self.x, self.y = nx, ny
        self.move_timer = PLAYER_MOVE_DELAY
        return True

    def attack(self, target_pos, zone):
        weapon = self.inventory.current_weapon
        if weapon is None:
            return "무기가 없습니다! 미로에서 무기를 주우세요."
        return weapon.attack(self, target_pos, zone)

    def drink_potion(self):
        inv = self.inventory
        if inv.potions <= 0:
            return "물약이 없습니다."
        if self.hp >= self.max_hp:
            return "체력이 가득 찼습니다."
        inv.potions -= 1
        self.heal(math.ceil(self.max_hp * POTION_HEAL_RATIO))
        return "물약을 마셨다! (+50%)"

    def draw(self, surf):
        cx, cy = self.screen_center()
        color = WHITE if self.hurt_timer > 0 else BLUE
        pygame.draw.circle(surf, color, (cx, cy), TILE // 2 - 4)
        fx, fy = self.facing
        pygame.draw.circle(surf, WHITE, (cx + fx * 7, cy + fy * 7), 3)
        weapon = self.inventory.current_weapon
        if weapon:
            weapon.draw_effect(surf, self)


class Monster(Entity):
    """밤에 등장하는 괴물. 근접 공격 + 직선 시야에서 독침 발사."""

    def __init__(self, x, y, rng):
        super().__init__(x, y, MONSTER_MAX_HP)
        self.rng = rng
        self.move_timer = rng.uniform(0, MONSTER_MOVE_DELAY)
        self.melee_timer = 0.0
        self.ranged_timer = MONSTER_RANGED_COOLDOWN

    def update(self, dt, zone, player):
        self.update_timers(dt)
        self.move_timer -= dt
        self.melee_timer -= dt
        self.ranged_timer -= dt

        distance = abs(self.x - player.x) + abs(self.y - player.y)

        # 1) 바로 옆이면 근접 공격 (쿨타임 있음)
        if distance == 1:
            if self.melee_timer <= 0:
                player.take_damage(MONSTER_MELEE_DAMAGE)
                self.melee_timer = MONSTER_MELEE_COOLDOWN
            return

        # 2) 직선 시야에 들어오면 독침
        if self.ranged_timer <= 0 and self._has_line_of_sight(player, zone):
            mx, my = self.world_center()
            px, py = player.world_center()
            zone.projectiles.append(PoisonDart(mx, my, px - mx, py - my))
            self.ranged_timer = MONSTER_RANGED_COOLDOWN

        # 3) 이동: 가까우면 추적, 아니면 배회
        if self.move_timer <= 0:
            self.move_timer = MONSTER_MOVE_DELAY
            step, path_len = zone.maze.next_step((self.x, self.y), (player.x, player.y))
            if step is None or path_len > MONSTER_DETECT_RANGE:
                options = [(self.x + dx, self.y + dy) for dx, dy in DIRECTIONS
                           if not zone.maze.is_wall(self.x + dx, self.y + dy)]
                step = self.rng.choice(options) if options else None
            if step and step != (player.x, player.y) and not zone.monster_at(*step):
                self.x, self.y = step

    def _has_line_of_sight(self, player, zone):
        if self.x == player.x:
            lo, hi = sorted((self.y, player.y))
            cells = [(self.x, y) for y in range(lo + 1, hi)]
        elif self.y == player.y:
            lo, hi = sorted((self.x, player.x))
            cells = [(x, self.y) for x in range(lo + 1, hi)]
        else:
            return False
        if len(cells) + 1 > MONSTER_RANGED_RANGE:
            return False
        return not any(zone.maze.is_wall(cx, cy) for cx, cy in cells)

    def knockback(self, direction, zone, player):
        nx, ny = self.x + direction[0], self.y + direction[1]
        if zone.maze.is_wall(nx, ny) or zone.monster_at(nx, ny) or (nx, ny) == (player.x, player.y):
            return
        self.x, self.y = nx, ny
        self.move_timer = MONSTER_MOVE_DELAY  # 밀려나면 잠깐 경직

    def draw(self, surf):
        cx, cy = self.screen_center()
        color = WHITE if self.hurt_timer > 0 else MONSTER_COLOR
        rect = pygame.Rect(0, 0, TILE - 6, TILE - 6)
        rect.center = (cx, cy)
        pygame.draw.rect(surf, color, rect, border_radius=6)
        pygame.draw.circle(surf, RED, (cx - 5, cy - 3), 3)
        pygame.draw.circle(surf, RED, (cx + 5, cy - 3), 3)
        self.draw_hp_bar(surf)
