"""무기, 열쇠, 인벤토리, 그리고 바닥에 떨어진 아이템(Pickup)."""
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pygame

from settings import (TILE, HUD_HEIGHT, ZONE_COUNT, SPEAR_DAMAGE, SPEAR_COOLDOWN,
                      SPEAR_KNOCKBACK, BOW_DAMAGE, BOW_COOLDOWN, BOW_START_ARROWS,
                      WHITE, RED, GOLD, YELLOW)
from projectiles import Arrow


# =====================================================================
# 무기
# =====================================================================
class Weapon(ABC):
    """모든 무기의 부모 클래스. attack()을 각자 다르게 구현한다(다형성)."""
    name = "weapon"
    display_name = "무기"
    damage = 0
    cooldown = 0.5

    def __init__(self):
        self.timer = 0.0

    @property
    def ready(self):
        return self.timer <= 0

    def update(self, dt):
        self.timer = max(0.0, self.timer - dt)

    def merge(self, other):
        """같은 무기를 또 주웠을 때. None이면 줍지 않음."""
        return None

    @abstractmethod
    def attack(self, player, target_pos, zone):
        """target_pos: 마우스 위치(월드 px). 메시지(str)나 None 반환."""

    def draw_effect(self, surf, player):
        pass

    def label(self):
        return self.display_name


class Spear(Weapon):
    name = "spear"
    display_name = "창"
    damage = SPEAR_DAMAGE
    cooldown = SPEAR_COOLDOWN

    def __init__(self):
        super().__init__()
        self.swing_timer = 0.0

    def update(self, dt):
        super().update(dt)
        self.swing_timer = max(0.0, self.swing_timer - dt)

    def attack(self, player, target_pos, zone):
        if not self.ready:
            return None
        px, py = player.world_center()
        dx, dy = target_pos[0] - px, target_pos[1] - py
        # 마우스 방향 중 더 큰 축으로 4방향 공격
        if abs(dx) >= abs(dy):
            direction = (1 if dx > 0 else -1, 0)
        else:
            direction = (0, 1 if dy > 0 else -1)
        player.facing = direction
        self.timer = self.cooldown
        self.swing_timer = 0.15

        monster = zone.monster_at(player.x + direction[0], player.y + direction[1])
        if monster:
            monster.take_damage(self.damage)
            for _ in range(SPEAR_KNOCKBACK):
                monster.knockback(direction, zone, player)
        return None

    def draw_effect(self, surf, player):
        if self.swing_timer <= 0:
            return
        cx, cy = player.screen_center()
        fx, fy = player.facing
        end = (cx + fx * TILE * 1.2, cy + fy * TILE * 1.2)
        pygame.draw.line(surf, YELLOW, (cx, cy), end, 4)


class Bow(Weapon):
    name = "bow"
    display_name = "활"
    damage = BOW_DAMAGE
    cooldown = BOW_COOLDOWN

    def __init__(self, arrows=BOW_START_ARROWS):
        super().__init__()
        self.arrows = arrows

    def merge(self, other):
        self.arrows += other.arrows
        return f"화살 +{other.arrows}"

    def attack(self, player, target_pos, zone):
        if not self.ready:
            return None
        if self.arrows <= 0:
            return "화살이 없습니다!"
        px, py = player.world_center()
        dx, dy = target_pos[0] - px, target_pos[1] - py
        if math.hypot(dx, dy) < 1:
            return None
        self.arrows -= 1
        self.timer = self.cooldown
        zone.projectiles.append(Arrow(px, py, dx, dy))
        return None

    def label(self):
        return f"{self.display_name} x{self.arrows}"


# =====================================================================
# 열쇠
# =====================================================================
@dataclass
class Key:
    zone_id: int   # 이 열쇠로 열 수 있는 탈출구가 있는 구역
    code: str      # 열쇠에 적힌 비밀번호

    @classmethod
    def random(cls, rng=random):
        return cls(rng.randint(1, ZONE_COUNT), f"{rng.randint(0, 9999):04d}")


# =====================================================================
# 인벤토리
# =====================================================================
class Inventory:
    SLOT_ORDER = ("spear", "bow")   # 숫자키 1, 2

    def __init__(self):
        self.weapons = {}
        self.current = None
        self.potions = 0
        self.key = None

    @property
    def current_weapon(self):
        return self.weapons.get(self.current)

    def add_weapon(self, weapon):
        existing = self.weapons.get(weapon.name)
        if existing:
            return existing.merge(weapon)
        self.weapons[weapon.name] = weapon
        if self.current is None:
            self.current = weapon.name
        return f"{weapon.display_name} 획득!"

    def select(self, name):
        if name in self.weapons:
            self.current = name
            return f"{self.weapons[name].display_name} 장착"
        return None

    def select_slot(self, index):
        if 0 <= index < len(self.SLOT_ORDER):
            return self.select(self.SLOT_ORDER[index])
        return None

    def cycle(self):
        owned = [n for n in self.SLOT_ORDER if n in self.weapons]
        if not owned:
            return None
        i = owned.index(self.current) if self.current in owned else -1
        return self.select(owned[(i + 1) % len(owned)])

    def update(self, dt):
        for w in self.weapons.values():
            w.update(dt)


# =====================================================================
# 바닥 아이템 (지나가면 자동 습득)
# =====================================================================
class Pickup(ABC):
    color = WHITE

    def __init__(self, x, y):
        self.x, self.y = x, y

    @abstractmethod
    def apply(self, player):
        """습득 성공 시 메시지(str), 줍지 않으면 None."""

    def rect(self):
        pad = 8
        return pygame.Rect(self.x * TILE + pad, HUD_HEIGHT + self.y * TILE + pad,
                           TILE - pad * 2, TILE - pad * 2)

    def draw(self, surf, font):
        pygame.draw.rect(surf, self.color, self.rect(), border_radius=4)


class WeaponPickup(Pickup):
    def __init__(self, x, y, weapon_cls):
        super().__init__(x, y)
        self.weapon_cls = weapon_cls
        self.color = (200, 200, 120) if weapon_cls is Spear else (160, 110, 60)

    def apply(self, player):
        return player.inventory.add_weapon(self.weapon_cls())

    def draw(self, surf, font):
        r = self.rect()
        if self.weapon_cls is Spear:
            pygame.draw.line(surf, self.color, r.bottomleft, r.topright, 4)
            pygame.draw.polygon(surf, WHITE, [r.topright, (r.right - 7, r.top + 2), (r.right - 2, r.top + 7)])
        else:
            pygame.draw.arc(surf, self.color, r, -1.3, 1.3, 3)
            pygame.draw.line(surf, WHITE, (r.centerx + 3, r.top + 2), (r.centerx + 3, r.bottom - 2), 1)


class PotionPickup(Pickup):
    color = RED

    def apply(self, player):
        player.inventory.potions += 1
        return "물약 획득!"

    def draw(self, surf, font):
        r = self.rect()
        pygame.draw.circle(surf, self.color, r.center, r.width // 2)
        pygame.draw.rect(surf, WHITE, (r.centerx - 3, r.top - 4, 6, 6))


class KeyPickup(Pickup):
    color = GOLD

    def __init__(self, x, y, key):
        super().__init__(x, y)
        self.key = key

    def apply(self, player):
        if player.inventory.key is not None:
            return None   # 열쇠는 하나만 소지
        player.inventory.key = self.key
        return f"열쇠 획득! [{self.key.zone_id}구역 / 코드 {self.key.code}]"

    def draw(self, surf, font):
        r = self.rect()
        pygame.draw.circle(surf, self.color, (r.left + 5, r.centery), 5, 2)
        pygame.draw.line(surf, self.color, (r.left + 10, r.centery), (r.right, r.centery), 3)
        pygame.draw.line(surf, self.color, (r.right - 3, r.centery), (r.right - 3, r.centery + 5), 2)
