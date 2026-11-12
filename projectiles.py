"""투사체: 플레이어의 화살, 괴물의 독침."""
import math
import pygame

from settings import (TILE, HUD_HEIGHT, ARROW_SPEED, BOW_DAMAGE, DART_SPEED,
                      MONSTER_RANGED_DAMAGE, WHITE, PURPLE)


class Projectile:
    """직선으로 날아가다 벽이나 대상에 닿으면 사라지는 투사체 (월드 좌표 px 기준)."""

    def __init__(self, x, y, dx, dy, speed, damage, from_player, color, radius):
        length = math.hypot(dx, dy) or 1
        self.x, self.y = x, y
        self.vx, self.vy = dx / length * speed, dy / length * speed
        self.damage = damage
        self.from_player = from_player
        self.color = color
        self.radius = radius
        self.alive = True

    @property
    def tile(self):
        return int(self.x // TILE), int(self.y // TILE)

    def update(self, dt, zone, player):
        self.x += self.vx * dt
        self.y += self.vy * dt
        tx, ty = self.tile
        if zone.maze.is_wall(tx, ty):
            self.alive = False
            return
        if self.from_player:
            target = zone.monster_at(tx, ty)
        else:
            target = player if (player.x, player.y) == (tx, ty) else None
        if target is not None:
            target.take_damage(self.damage)
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y) + HUD_HEIGHT), self.radius)


class Arrow(Projectile):
    def __init__(self, x, y, dx, dy):
        super().__init__(x, y, dx, dy, ARROW_SPEED, BOW_DAMAGE, True, WHITE, 3)

    def draw(self, surf):
        # 진행 방향으로 짧은 선을 그려서 화살처럼 보이게
        speed = math.hypot(self.vx, self.vy) or 1
        tail = (self.x - self.vx / speed * 10, self.y - self.vy / speed * 10 + HUD_HEIGHT)
        pygame.draw.line(surf, self.color, tail, (self.x, self.y + HUD_HEIGHT), 2)


class PoisonDart(Projectile):
    def __init__(self, x, y, dx, dy, damage=MONSTER_RANGED_DAMAGE):
        super().__init__(x, y, dx, dy, DART_SPEED, damage, False, PURPLE, 4)
