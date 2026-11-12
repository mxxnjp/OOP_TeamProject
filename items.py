"""무기, 열쇠, 인벤토리, 그리고 바닥에 떨어진 아이템(Pickup)."""
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pygame

from settings import (TILE, HUD_HEIGHT, SPEAR_DAMAGE, SPEAR_COOLDOWN,
                      SPEAR_KNOCKBACK, BOW_DAMAGE, BOW_COOLDOWN, BOW_START_ARROWS,
                      ITEM_SPRITES, ITEM_SPRITE_SIZE, SPEAR_SWING_SIZE, SPEAR_SPRITE_ANGLE,
                      WHITE, RED, YELLOW)
from projectiles import Arrow
from themes import load_sprite, rotated_sprite


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
        # 창 그림을 바라보는 방향으로 돌려서 한 칸 앞에 찌르듯이 그림
        heading = math.degrees(math.atan2(-fy, fx))
        img = rotated_sprite(ITEM_SPRITES["spear"], SPEAR_SWING_SIZE, heading - SPEAR_SPRITE_ANGLE)
        if img:
            surf.blit(img, img.get_rect(center=(cx + fx * TILE * 0.8, cy + fy * TILE * 0.8)))
            return
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
@dataclass(frozen=True)
class Key:
    zone_id: int   # 이 키를 얻은 구역 (구역마다 1개, 총 4개)


# =====================================================================
# 인벤토리
# =====================================================================
class Inventory:
    SLOT_ORDER = ("spear", "bow")   # 숫자키 1, 2

    def __init__(self):
        self.weapons = {}
        self.current = None
        self.potions = 0
        self.keys = set()   # 얻은 Key들 (구역마다 하나)

    @property
    def current_weapon(self):
        return self.weapons.get(self.current)

    def add_key(self, key):
        self.keys.add(key)
        return len(self.keys)

    def has_key_for(self, zone_id):
        return Key(zone_id) in self.keys

    @property
    def key_count(self):
        return len(self.keys)

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

    def update(self, dt):
        for w in self.weapons.values():
            w.update(dt)


# =====================================================================
# 바닥 아이템 (지나가면 자동 습득)
# =====================================================================
class Pickup(ABC):
    color = WHITE
    sprite_key = None   # ITEM_SPRITES의 키. 그림이 있으면 그림, 없으면 draw_shape()

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
        img = load_sprite(ITEM_SPRITES.get(self.sprite_key), ITEM_SPRITE_SIZE) if self.sprite_key else None
        if img:
            surf.blit(img, img.get_rect(center=self.rect().center))
        else:
            self.draw_shape(surf)

    def draw_shape(self, surf):
        """그림 파일이 없을 때 쓰는 도형."""
        pygame.draw.rect(surf, self.color, self.rect(), border_radius=4)


class WeaponPickup(Pickup):
    def __init__(self, x, y, weapon_cls):
        super().__init__(x, y)
        self.weapon_cls = weapon_cls
        self.sprite_key = weapon_cls.name
        self.color = (200, 200, 120) if weapon_cls is Spear else (160, 110, 60)

    def apply(self, player):
        return player.inventory.add_weapon(self.weapon_cls())

    def draw_shape(self, surf):
        r = self.rect()
        if self.weapon_cls is Spear:
            pygame.draw.line(surf, self.color, r.bottomleft, r.topright, 4)
            pygame.draw.polygon(surf, WHITE, [r.topright, (r.right - 7, r.top + 2), (r.right - 2, r.top + 7)])
        else:
            pygame.draw.arc(surf, self.color, r, -1.3, 1.3, 3)
            pygame.draw.line(surf, WHITE, (r.centerx + 3, r.top + 2), (r.centerx + 3, r.bottom - 2), 1)


class PotionPickup(Pickup):
    color = RED
    sprite_key = "potion"

    def apply(self, player):
        player.inventory.potions += 1
        return "물약 획득!"

    def draw_shape(self, surf):
        r = self.rect()
        pygame.draw.circle(surf, self.color, r.center, r.width // 2)
        pygame.draw.rect(surf, WHITE, (r.centerx - 3, r.top - 4, 6, 6))
