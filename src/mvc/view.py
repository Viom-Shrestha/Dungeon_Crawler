import os
import random
import time
from typing import Dict, List, Optional, Tuple

import pygame

from game_engine import TileType
from mvc.constants import (
    ASSETS_DIR,
    BLACK,
    BLUE,
    BROWN,
    DARK_GRAY,
    GOLD,
    GREEN,
    LIGHT_GRAY,
    MAX_LEVELS,
    ORANGE,
    PURPLE,
    RED,
    TILE_SIZE,
    UI_PANEL_WIDTH,
    WHITE,
    YELLOW,
    GameState,
)
from mvc.model import GameModel


class Button:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: Tuple[int, int, int],
        hover_color: Tuple[int, int, int],
        font_size: int = 24,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = pygame.font.Font(None, font_size)
        self.hovered = False

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.current_color = self.hover_color
                self.hovered = True
            else:
                self.current_color = self.color
                self.hovered = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                return True
        return False


def safe_load_sprite(
    path: str,
    fallback_color: Tuple[int, int, int] = (0, 0, 255),
    size: Optional[Tuple[int, int]] = (TILE_SIZE, TILE_SIZE),
) -> pygame.Surface:
    try:
        img = pygame.image.load(path)
        has_per_pixel_alpha = (img.get_alpha() is not None) or (img.get_masks()[3] != 0)
        img = img.convert_alpha() if has_per_pixel_alpha else img.convert()
        if not has_per_pixel_alpha:
            img.set_colorkey(img.get_at((0, 0)))
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    except Exception:
        surface = pygame.Surface(size or (TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        surface.fill(fallback_color)
        return surface


class GameView:
    """View layer: all rendering and UI hit-testing."""

    def __init__(self, model: GameModel):
        self.model = model

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption("Dungeon Crawler - GUI Version (MVC)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 64)

        self.menu_buttons: List[Button] = []
        self.play_buttons: List[Button] = []
        self.quit_button: Optional[Button] = None

        self.menu_bg = pygame.Surface((self.width, self.height))
        self.menu_bg.fill((18, 18, 24))
        self.floor_tiles: List[pygame.Surface] = []
        self.tile_variants: List[List[int]] = []
        self.wall_solid = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.monster_sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.monster_sprite.fill(RED)
        self.chest_sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.stairs_sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))

        self.player_sprites: Dict[str, pygame.Surface] = {}
        self.player2_sprites: Dict[str, pygame.Surface] = {}
        self.player_sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.player2_sprite = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.monster_sprites: Dict[str, pygame.Surface] = {}

        self.load_sprites()
        self.create_menu_buttons()
        self.create_play_buttons()
        self.rebuild_tile_variants()

    # ---------- Setup ----------
    def load_sprites(self) -> None:
        bg_path = os.path.join(ASSETS_DIR, "background.jpg")
        self.menu_bg = safe_load_sprite(bg_path, (18, 18, 24), size=(self.width, self.height))

        self.floor_tiles = []
        for i in range(1, 4):
            path = os.path.join(ASSETS_DIR, f"tile{i}.png")
            tile = safe_load_sprite(path, LIGHT_GRAY, (TILE_SIZE, TILE_SIZE))
            self.floor_tiles.append(tile)

        self.wall_solid = safe_load_sprite(os.path.join(ASSETS_DIR, "wall.png"), BROWN, (TILE_SIZE, TILE_SIZE))
        self.chest_sprite = safe_load_sprite(os.path.join(ASSETS_DIR, "chest.png"), YELLOW, (TILE_SIZE, TILE_SIZE))
        self.stairs_sprite = safe_load_sprite(os.path.join(ASSETS_DIR, "stairs.png"), PURPLE, (TILE_SIZE, TILE_SIZE))

        for direction in ["up", "down", "left", "right"]:
            p1_path = os.path.join(ASSETS_DIR, f"player_{direction}.png")
            self.player_sprites[direction] = safe_load_sprite(p1_path, BLUE, (TILE_SIZE, TILE_SIZE))

        fallback_p1 = safe_load_sprite(os.path.join(ASSETS_DIR, "player.png"), BLUE, (TILE_SIZE, TILE_SIZE))
        for direction in ["up", "down", "left", "right"]:
            self.player_sprites[direction] = self.player_sprites.get(direction) or fallback_p1
        self.player_sprite = self.player_sprites["down"]

        for direction in ["up", "down", "left", "right"]:
            p2_path = os.path.join(ASSETS_DIR, f"player2_{direction}.png")
            self.player2_sprites[direction] = safe_load_sprite(p2_path, (0, 220, 200), (TILE_SIZE, TILE_SIZE))

        fallback_p2 = safe_load_sprite(os.path.join(ASSETS_DIR, "player2.png"), (0, 220, 200), (TILE_SIZE, TILE_SIZE))
        for direction in ["up", "down", "left", "right"]:
            self.player2_sprites[direction] = self.player2_sprites.get(direction) or fallback_p2
        self.player2_sprite = self.player2_sprites["down"]

        self.reload_monster_sprites()

    def reload_monster_sprites(self) -> None:
        self.monster_sprites = {}
        for name, monster in self.model.monsters.items():
            sprite_name = getattr(monster, "sprite", None)
            if sprite_name:
                path = os.path.join(ASSETS_DIR, sprite_name)
                surface = safe_load_sprite(path, RED, (TILE_SIZE, TILE_SIZE))
            else:
                surface = self.monster_sprite
            self.monster_sprites[name] = pygame.transform.scale(surface, (TILE_SIZE, TILE_SIZE))

    def rebuild_tile_variants(self) -> None:
        tile_count = max(1, len(self.floor_tiles))
        self.tile_variants = [
            [random.randint(0, tile_count - 1) for _ in range(self.model.game_map.width)]
            for _ in range(self.model.game_map.height)
        ]

    def create_menu_buttons(self) -> None:
        cx = self.width // 2
        start_y = self.height // 2 - 40
        self.menu_buttons = [
            Button(cx - 120, start_y - 120, 240, 50, "Start Game", GREEN, (0, 200, 0), 36),
            Button(
                cx - 120,
                start_y - 40,
                240,
                50,
                f"Difficulty: {self.model.difficulties[self.model.difficulty_index].capitalize()}",
                BLUE,
                (0, 0, 200),
                32,
            ),
            Button(
                cx - 120,
                start_y + 40,
                240,
                50,
                f"Multiplayer: {'On' if self.model.multiplayer else 'Off'}",
                ORANGE,
                (200, 120, 0),
                32,
            ),
            Button(cx - 120, start_y + 120, 240, 50, "Quit", RED, (200, 0, 0), 36),
        ]

    def create_play_buttons(self) -> None:
        btn_y = self.height - 100
        self.play_buttons = [
            Button(50, btn_y, 120, 40, "Inventory", BLUE, (0, 0, 200)),
            Button(180, btn_y, 100, 40, "Quests", PURPLE, (150, 0, 150)),
            Button(290, btn_y, 100, 40, "Undo", ORANGE, (220, 140, 0)),
        ]
        self.quit_button = Button(self.width - 110, self.height - 60, 90, 40, "Quit", RED, (200, 0, 0))

    def set_actor_direction(self, actor_index: int, dx: int, dy: int) -> None:
        if dx == 1:
            direction = "right"
        elif dx == -1:
            direction = "left"
        elif dy == -1:
            direction = "up"
        else:
            direction = "down"

        if actor_index == 1:
            self.player_sprite = self.player_sprites[direction]
        else:
            self.player2_sprite = self.player2_sprites[direction]

    # ---------- Hit Testing ----------
    def get_inventory_layout(self) -> Dict[str, int]:
        panel_x = self.width // 2 - 250
        panel_y = self.height // 2 - 250
        panel_w = 500
        panel_h = 550
        eq_y = panel_y + 125
        viewport_y = eq_y + 70
        viewport_h = panel_h - (viewport_y - panel_y) - 40
        return {
            "panel_x": panel_x,
            "panel_y": panel_y,
            "panel_w": panel_w,
            "panel_h": panel_h,
            "eq_y": eq_y,
            "viewport_y": viewport_y,
            "viewport_h": viewport_h,
        }

    def max_inventory_scroll(self) -> int:
        item_count = len(self.model.player.inventory)
        viewport_h = self.get_inventory_layout()["viewport_h"]
        return max(0, item_count * self.model.inventory_row_height - viewport_h)

    def inventory_item_index_at(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        if not self.model.show_inventory:
            return None

        layout = self.get_inventory_layout()
        panel_x = layout["panel_x"]
        panel_w = layout["panel_w"]
        viewport_y = layout["viewport_y"]
        viewport_h = layout["viewport_h"]

        if not (panel_x <= mouse_pos[0] <= panel_x + panel_w and viewport_y <= mouse_pos[1] <= viewport_y + viewport_h):
            return None

        items = self.model.player.inventory
        if not items:
            return None

        start_index = max(0, self.model.scroll_offset // self.model.inventory_row_height)
        visible_rows = viewport_h // self.model.inventory_row_height + 1
        end_index = min(len(items), start_index + visible_rows)

        for idx in range(start_index, end_index):
            row_y = viewport_y + (idx - start_index) * self.model.inventory_row_height
            row_rect = pygame.Rect(panel_x + 20, row_y, panel_w - 40, self.model.inventory_row_height - 8)
            if row_rect.collidepoint(mouse_pos):
                return idx
        return None

    # ---------- Drawing ----------
    def _draw_tile_at_screen(self, x: int, y: int, tile_type: str, visible: bool, screen_x: int, screen_y: int) -> None:
        if not visible:
            pygame.draw.rect(self.screen, DARK_GRAY, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
            return

        idx = self.tile_variants[y][x]
        self.screen.blit(self.floor_tiles[idx], (screen_x, screen_y))

        if tile_type == TileType.WALL.value:
            self.screen.blit(self.wall_solid, (screen_x, screen_y))
            return

        if tile_type == TileType.TREASURE.value:
            self.screen.blit(self.chest_sprite, (screen_x, screen_y))
            return

        if tile_type.startswith(TileType.MONSTER.value):
            parts = tile_type.split(":")
            if len(parts) > 1:
                monster_name = parts[1]
            else:
                pool = [k for k in self.model.monsters.keys() if k != "dragon"] or list(self.model.monsters.keys())
                monster_name = random.choice(pool)
                self.model.game_map.set_tile(x, y, f"{TileType.MONSTER.value}:{monster_name}")

            sprite = self.monster_sprites.get(monster_name, self.monster_sprite)
            self.screen.blit(sprite, (screen_x, screen_y))
            return

        if tile_type == TileType.STAIRS_DOWN.value:
            self.screen.blit(self.stairs_sprite, (screen_x, screen_y))

    def draw_map(self) -> None:
        tiles_x = self.width // TILE_SIZE + 2
        tiles_y = self.height // TILE_SIZE + 2

        cam_x = self.model.player.x * TILE_SIZE - self.width // 2 + TILE_SIZE // 2
        cam_y = self.model.player.y * TILE_SIZE - self.height // 2 + TILE_SIZE // 2

        max_cam_x = self.model.game_map.width * TILE_SIZE - self.width
        max_cam_y = self.model.game_map.height * TILE_SIZE - self.height
        cam_x = max(0, min(cam_x, max_cam_x))
        cam_y = max(0, min(cam_y, max_cam_y))

        start_x = max(0, cam_x // TILE_SIZE)
        end_x = min(self.model.game_map.width, start_x + tiles_x)
        start_y = max(0, cam_y // TILE_SIZE)
        end_y = min(self.model.game_map.height, start_y + tiles_y)

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_type = self.model.game_map.get_tile(x, y)
                visible = self.model.game_map.visible_map[y][x]
                screen_x = x * TILE_SIZE - cam_x
                screen_y = y * TILE_SIZE - cam_y
                self._draw_tile_at_screen(x, y, tile_type, visible, screen_x, screen_y)

        px = self.model.player.x * TILE_SIZE - cam_x
        py = self.model.player.y * TILE_SIZE - cam_y
        self.screen.blit(self.player_sprite, (px, py))

        if self.model.multiplayer:
            p2x = self.model.player2.x * TILE_SIZE - cam_x
            p2y = self.model.player2.y * TILE_SIZE - cam_y
            self.screen.blit(self.player2_sprite, (p2x, p2y))

    def draw_ui_panel(self) -> None:
        panel_x = self.width - UI_PANEL_WIDTH
        panel_y = 0
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, UI_PANEL_WIDTH, self.height))
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, UI_PANEL_WIDTH, self.height), 2)

        title = self.large_font.render(f"Level {self.model.game_map.current_level}/{MAX_LEVELS}", True, WHITE)
        self.screen.blit(title, (panel_x + 20, 20))

        if self.model.start_time and self.model.state == GameState.PLAYING:
            self.model.run_time = time.time() - self.model.start_time

        stats_y = 80
        stats = [
            f"Health: {self.model.player.health}/{self.model.player.max_health}",
            f"Lvl: {self.model.player.level}  EXP: {self.model.player.experience}",
            f"Gold: {self.model.player.gold}",
            f"ATK: {self.model.player.attack}  DEF: {self.model.player.defense}",
            f"Time: {self.model.run_time:.1f}s",
        ]

        if self.model.multiplayer:
            stats.extend(
                [
                    f"P2 Health: {self.model.player2.health}/{self.model.player2.max_health}",
                    f"P2 Lvl: {self.model.player2.level}  EXP: {self.model.player2.experience}",
                    f"P2 ATK: {self.model.player2.attack}  DEF: {self.model.player2.defense}",
                ]
            )

        for stat in stats:
            text = self.font.render(stat, True, WHITE)
            self.screen.blit(text, (panel_x + 20, stats_y))
            stats_y += 25

        health_bar_x = panel_x + 20
        health_bar_y = stats_y + 10
        health_bar_width = UI_PANEL_WIDTH - 40
        health_bar_height = 18

        pygame.draw.rect(self.screen, RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        hw1 = int((self.model.player.health / max(1, self.model.player.max_health)) * health_bar_width)
        pygame.draw.rect(self.screen, GREEN, (health_bar_x, health_bar_y, hw1, health_bar_height))
        pygame.draw.rect(self.screen, BLACK, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)
        p1_label = self.font.render(f"P1 {self.model.player.health}/{self.model.player.max_health}", True, BLACK)
        self.screen.blit(p1_label, (health_bar_x + 6, health_bar_y + 1))

        if self.model.multiplayer:
            health_bar_y2 = health_bar_y + health_bar_height + 8
            pygame.draw.rect(self.screen, RED, (health_bar_x, health_bar_y2, health_bar_width, health_bar_height))
            hw2 = int((self.model.player2.health / max(1, self.model.player2.max_health)) * health_bar_width)
            pygame.draw.rect(self.screen, GREEN, (health_bar_x, health_bar_y2, hw2, health_bar_height))
            pygame.draw.rect(self.screen, BLACK, (health_bar_x, health_bar_y2, health_bar_width, health_bar_height), 2)
            p2_label = self.font.render(f"P2 {self.model.player2.health}/{self.model.player2.max_health}", True, BLACK)
            self.screen.blit(p2_label, (health_bar_x + 6, health_bar_y2 + 1))
            message_y = health_bar_y2 + health_bar_height + 22
        else:
            message_y = health_bar_y + health_bar_height + 30

        self.screen.blit(self.font.render("Messages:", True, WHITE), (panel_x + 20, message_y))
        if self.model.message_log:
            messages = self.model.message_log[-5:]
            message_y += 30
            for message in messages:
                words = message.split(" ")
                current_line = ""
                for word in words:
                    test_line = current_line + word + " "
                    if self.font.size(test_line)[0] > UI_PANEL_WIDTH - 40:
                        line_surface = self.font.render(f"- {current_line.strip()}", True, LIGHT_GRAY)
                        self.screen.blit(line_surface, (panel_x + 20, message_y))
                        message_y += self.font.get_height() + 2
                        current_line = word + " "
                    else:
                        current_line = test_line
                if current_line:
                    line_surface = self.font.render(f"- {current_line.strip()}", True, LIGHT_GRAY)
                    self.screen.blit(line_surface, (panel_x + 20, message_y))
                    message_y += self.font.get_height() + 2

    def draw_buttons(self) -> None:
        for button in self.play_buttons:
            button.draw(self.screen)
        if self.quit_button:
            self.quit_button.draw(self.screen)

    def draw_inventory(self) -> None:
        if not self.model.show_inventory:
            return

        layout = self.get_inventory_layout()
        panel_x = layout["panel_x"]
        panel_y = layout["panel_y"]
        panel_w = layout["panel_w"]
        panel_h = layout["panel_h"]
        eq_y = layout["eq_y"]
        viewport_y = layout["viewport_y"]
        viewport_h = layout["viewport_h"]

        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        title = self.large_font.render("Inventory", True, WHITE)
        self.screen.blit(title, (panel_x + 20, panel_y + 15))

        hint1 = self.font.render("ESC to close | Scroll to navigate", True, LIGHT_GRAY)
        hint2 = self.font.render("Left click = use/equip | Right click = sell", True, LIGHT_GRAY)
        self.screen.blit(hint1, (panel_x + 20, panel_y + 50))
        self.screen.blit(hint2, (panel_x + 20, panel_y + 70))

        target_label = f"Active target: {self.model.inventory_target_names[self.model.active_player]} (Press 1/2)"
        self.screen.blit(self.font.render(target_label, True, YELLOW), (panel_x + 20, panel_y + 90))

        p1_weapon = self.model.player.equipped_weapon.name if self.model.player.equipped_weapon else "None"
        p1_armor = self.model.player.equipped_armor.name if self.model.player.equipped_armor else "None"
        self.screen.blit(self.font.render(f"P1 Weapon: {p1_weapon}", True, WHITE), (panel_x + 20, eq_y))
        self.screen.blit(self.font.render(f"P1 Armor:  {p1_armor}", True, WHITE), (panel_x + 20, eq_y + 20))

        if self.model.multiplayer:
            p2_weapon = self.model.player2.equipped_weapon.name if self.model.player2.equipped_weapon else "None"
            p2_armor = self.model.player2.equipped_armor.name if self.model.player2.equipped_armor else "None"
            self.screen.blit(self.font.render(f"P2 Weapon: {p2_weapon}", True, WHITE), (panel_x + 260, eq_y))
            self.screen.blit(self.font.render(f"P2 Armor:  {p2_armor}", True, WHITE), (panel_x + 260, eq_y + 20))

        items = self.model.player.inventory
        start_index = max(0, self.model.scroll_offset // self.model.inventory_row_height)
        visible_rows = viewport_h // self.model.inventory_row_height + 1
        end_index = min(len(items), start_index + visible_rows)

        for idx in range(start_index, end_index):
            item = items[idx]
            row_y = viewport_y + (idx - start_index) * self.model.inventory_row_height
            row_rect = pygame.Rect(panel_x + 20, row_y, panel_w - 40, self.model.inventory_row_height - 8)
            pygame.draw.rect(self.screen, (80, 80, 80), row_rect, border_radius=6)
            pygame.draw.rect(self.screen, BLACK, row_rect, 1, border_radius=6)

            name = f"{item.name} ({item.item_type})"
            desc = item.description
            if item.item_type == "weapon":
                desc += f" | +{getattr(item, 'effect_value', 0)} ATK"
            elif item.item_type == "armor":
                desc += f" | +{getattr(item, 'effect_value', 0)} DEF"
            elif item.item_type == "consumable":
                desc += f" | Restores {getattr(item, 'effect_value', item.value)} HP"
            elif item.item_type == "treasure":
                desc += f" | Sell for {item.value} gold"

            text1 = self.font.render(name, True, WHITE)
            text2 = self.font.render(desc, True, LIGHT_GRAY)
            self.screen.blit(text1, (row_rect.x + 10, row_rect.y + 6))
            self.screen.blit(text2, (row_rect.x + 10, row_rect.y + 28))

        if len(items) * self.model.inventory_row_height > viewport_h:
            bar_h = max(30, int(viewport_h * viewport_h / (len(items) * self.model.inventory_row_height)))
            max_scroll = self.max_inventory_scroll()
            bar_y = viewport_y + int((self.model.scroll_offset / max(1, max_scroll)) * (viewport_h - bar_h))
            pygame.draw.rect(self.screen, LIGHT_GRAY, (panel_x + panel_w - 18, bar_y, 6, bar_h), border_radius=3)

    def draw_quests(self) -> None:
        if not self.model.show_quests:
            return

        panel_x = self.width // 2 - 250
        panel_y = self.height // 2 - 200
        panel_w = 500
        panel_h = 400
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)
        self.screen.blit(self.large_font.render("Quests", True, WHITE), (panel_x + 20, panel_y + 15))

        quests_y = panel_y + 70
        for i, quest in enumerate(self.model.quest_log.get_quests()):
            status = "Completed" if getattr(quest, "completed", False) else "In progress"
            qtext = f"{i + 1}. {quest.title} - {status}"
            self.screen.blit(self.font.render(qtext, True, WHITE), (panel_x + 20, quests_y))
            self.screen.blit(self.font.render(f"   {quest.description}", True, LIGHT_GRAY), (panel_x + 20, quests_y + 22))
            self.screen.blit(self.font.render(f"   Reward: {quest.reward}", True, YELLOW), (panel_x + 20, quests_y + 42))
            quests_y += 70

    def draw_loading(self) -> None:
        self.screen.fill(BLACK)
        text = self.title_font.render("Loading...", True, WHITE)
        self.screen.blit(text, text.get_rect(center=(self.width // 2, self.height // 2)))

    def draw_menu(self) -> None:
        self.screen.blit(self.menu_bg, (0, 0))
        title = self.title_font.render("Dungeon Crawler", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 140)))

        if self.model.highscore is not None:
            hs = self.font.render(f"Best Time: {self.model.highscore:.1f}s", True, LIGHT_GRAY)
            self.screen.blit(hs, hs.get_rect(center=(self.width // 2, 200)))

        for button in self.menu_buttons:
            button.draw(self.screen)

        hint = self.font.render("ESC to quit | Use mouse to select", True, LIGHT_GRAY)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 60)))

    def draw_game_over(self) -> None:
        self.screen.fill((30, 0, 0))
        line1 = self.title_font.render("You have fallen.", True, RED)
        line2 = self.font.render("Click or press any key to return to Main Menu", True, WHITE)
        self.screen.blit(line1, line1.get_rect(center=(self.width // 2, self.height // 2 - 40)))
        self.screen.blit(line2, line2.get_rect(center=(self.width // 2, self.height // 2 + 20)))

    def draw_victory(self) -> None:
        self.screen.fill((0, 30, 0))
        line1 = self.title_font.render("Dungeon Completed!", True, GOLD)
        if self.model.highscore:
            line2_text = f"Time: {self.model.run_time:.1f}s   Best: {self.model.highscore:.1f}s"
        else:
            line2_text = f"Time: {self.model.run_time:.1f}s"
        line2 = self.font.render(line2_text, True, WHITE)
        line3 = self.font.render("Click or press any key to return to Main Menu", True, WHITE)
        self.screen.blit(line1, line1.get_rect(center=(self.width // 2, self.height // 2 - 60)))
        self.screen.blit(line2, line2.get_rect(center=(self.width // 2, self.height // 2)))
        self.screen.blit(line3, line3.get_rect(center=(self.width // 2, self.height // 2 + 40)))

    def draw_playing(self) -> None:
        self.screen.fill(BLACK)
        self.draw_map()
        self.draw_ui_panel()
        self.draw_buttons()

        if self.model.show_inventory:
            self.draw_inventory()
        if self.model.show_quests:
            self.draw_quests()

        controls_text = "WASD / Arrows: Move | ESC: Close/Back"
        controls = self.font.render(controls_text, True, LIGHT_GRAY)
        self.screen.blit(controls, (20, self.height - 30))

