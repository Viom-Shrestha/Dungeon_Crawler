
import pygame
import random
import time
import os
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum, auto

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
TILE_SIZE = 32
UI_PANEL_WIDTH = 300
MAX_LEVELS = 10
ASSETS_DIR = "assets"
HIGHSCORE_FILE = "highscore.txt"

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)

# Import your existing classes
from dungeon_crawler import (
    Direction, TileType, Item, Monster, Quest, QuestNode, QuestLog,
    MoveStack, ActionQueue, Player, GameMap, DungeonCrawler
)

class GameState(Enum):
    LOADING = auto()
    MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    QUIT = auto()

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, text: str,
                color: Tuple[int, int, int], hover_color: Tuple[int, int, int], font_size: int = 24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = pygame.font.Font(None, font_size)
        self.hovered = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
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

def safe_load_sprite(path: str, fallback_color: Tuple[int, int, int] = BLUE) -> Optional[pygame.Surface]:
    try:
        surf = pygame.image.load(path).convert_alpha()
        return surf
    except Exception:
        # Fallback: colored square
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        s.fill(fallback_color)
        return s

class DungeonCrawlerGUI:
    def __init__(self, difficulty: str = "normal"):
        self.difficulty = difficulty
        self.map_size = self.get_map_size_by_difficulty()
        self.player = Player(1, 1)
        self.game_map = GameMap(self.map_size[0], self.map_size[1], difficulty)
        self.quest_log = QuestLog()
        self.move_stack = MoveStack()
        self.action_queue = ActionQueue()
        self.state = GameState.LOADING
        self.loading_start = time.time()
        self.loading_duration = 1.5  # seconds
        self.menu_buttons: List[Button] = []
        self.quit_button: Optional[Button] = None
        self.play_buttons: List[Button] = []  # inventory, quests, undo
        self.difficulty_index = {"easy": 0, "normal": 1, "hard": 2}.get(difficulty, 1)
        self.difficulties = ["easy", "normal", "hard"]
        self.message_log: List[str] = []
        self.scroll_offset = 0  # inventory scroll
        self.inventory_row_height = 64
        self.show_inventory = False
        self.show_quests = False
        self.start_time = None
        self.run_time = 0.0
        self.highscore = self.load_highscore()
        self.rewarded_quests = set()  # track rewards given
        self.boss_defeated = False

        # Pygame setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Crawler - GUI Version")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 64)

        # Sprites
        self.player_sprite = None
        self.monster_sprite = None
        self.chest_sprite = None
        self.stairs_sprite = None
        self.load_sprites()

        # Monster + Items (no doors/keys now)
        self.monsters = self.create_monsters()
        self.items = self.create_items()  # exclude keys
        self.initialize_quests()

        # UI buttons
        self.create_menu_buttons()
        self.create_play_buttons()

        # Reveal starting area & ensure valid map
        self.ensure_valid_map(initial=True)

    # ---------- Setup / Loading ----------
    def load_sprites(self):
        player_path = os.path.join(ASSETS_DIR, "player.png")
        monster_path = os.path.join(ASSETS_DIR, "monster.png")
        chest_path = os.path.join(ASSETS_DIR, "chest.png")
        stairs_path = os.path.join(ASSETS_DIR, "stairs.png")
        self.player_sprite = pygame.transform.scale(safe_load_sprite(player_path, BLUE), (TILE_SIZE, TILE_SIZE))
        self.monster_sprite = pygame.transform.scale(safe_load_sprite(monster_path, RED), (TILE_SIZE, TILE_SIZE))
        self.chest_sprite = pygame.transform.scale(safe_load_sprite(chest_path, YELLOW), (TILE_SIZE, TILE_SIZE))
        self.stairs_sprite = pygame.transform.scale(safe_load_sprite(stairs_path, PURPLE), (TILE_SIZE, TILE_SIZE))

    def load_highscore(self) -> Optional[float]:
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, "r") as f:
                    return float(f.read().strip())
        except Exception:
            pass
        return None

    def save_highscore(self, seconds: float):
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                f.write(str(seconds))
        except Exception:
            pass

    def get_map_size_by_difficulty(self) -> Tuple[int, int]:
        if self.difficulty == "easy":
            return (15, 10)
        elif self.difficulty == "hard":
            return (25, 20)
        else:  # normal
            return (20, 15)

    def create_monsters(self) -> Dict[str, Monster]:
        base_monsters = {
            "goblin": {"health": 30, "attack": 8, "defense": 3},
            "orc": {"health": 50, "attack": 12, "defense": 6},
            "troll": {"health": 70, "attack": 15, "defense": 8},
            "ogre": {"health": 80, "attack": 18, "defense": 10},
            "skeleton": {"health": 40, "attack": 10, "defense": 5},
            "dragon": {"health": 140, "attack": 24, "defense": 16}
        }

        scale_factor = 1.0
        if self.difficulty == "easy":
            scale_factor = 0.7
        elif self.difficulty == "hard":
            scale_factor = 1.5

        monsters = {}
        for name, stats in base_monsters.items():
            scaled_health = int(stats["health"] * scale_factor)
            scaled_attack = int(stats["attack"] * scale_factor)
            scaled_defense = int(stats["defense"] * scale_factor)
            monsters[name] = Monster(name, scaled_health, scaled_attack, scaled_defense)
        return monsters

    def create_items(self) -> Dict[str, Item]:
        # Removed keys. Treasures are marked with item_type="treasure" to be sold for gold.
        return {
            "sword": Item("Iron Sword", "A sharp iron sword", 50, "weapon", 5),
            "steel_sword": Item("Steel Sword", "A superior steel sword", 80, "weapon", 8),
            "magic_sword": Item("Magic Sword", "A sword with magical properties", 150, "weapon", 12),
            "shield": Item("Wooden Shield", "A sturdy wooden shield", 30, "armor", 3),
            "iron_shield": Item("Iron Shield", "A strong iron shield", 60, "armor", 6),
            "magic_shield": Item("Magic Shield", "A shield with magical protection", 120, "armor", 10),
            "potion": Item("Health Potion", "Restores 25 health", 25, "consumable", 25),
            "greater_potion": Item("Greater Health Potion", "Restores 50 health", 50, "consumable", 50),
            "super_potion": Item("Super Health Potion", "Restores 100 health", 100, "consumable", 100),
            "gem": Item("Precious Gem", "A valuable gemstone", 100, "treasure"),
            "ring": Item("Ring of Power", "Increases attack and defense", 200, "treasure"),
        }

    def initialize_quests(self):
        quest1 = Quest("Goblin Hunter", "Defeat 3 goblins", "goblin", "50 Gold")
        quest2 = Quest("Treasure Collector", "Collect 5 treasures", "treasure", "Rare weapon")
        quest3 = Quest("Dragon Slayer", "Defeat the dragon", "dragon", "Legendary armor")
        self.quest_log.add_quest(quest1)
        self.quest_log.add_quest(quest2)
        self.quest_log.add_quest(quest3)

    def create_menu_buttons(self):
        cx = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - 40
        self.menu_buttons = [
            Button(cx - 120, start_y - 80, 240, 50, "Start Game", GREEN, (0, 200, 0), 36),
            Button(cx - 120, start_y, 240, 50, f"Difficulty: {self.difficulties[self.difficulty_index].capitalize()}", BLUE, (0, 0, 200), 32),
            Button(cx - 120, start_y + 80, 240, 50, "Quit", RED, (200, 0, 0), 36),
        ]

    def create_play_buttons(self):
        btn_y = SCREEN_HEIGHT - 100
        self.play_buttons = [
            Button(50, btn_y, 120, 40, "Inventory", BLUE, (0, 0, 200)),
            Button(180, btn_y, 100, 40, "Quests", PURPLE, (150, 0, 150)),
            Button(290, btn_y, 100, 40, "Undo", ORANGE, (220, 140, 0)),
        ]
        # Bottom-right quit
        self.quit_button = Button(SCREEN_WIDTH - 110, SCREEN_HEIGHT - 60, 90, 40, "Quit", RED, (200, 0, 0))

    # ---------- Map / Flow ----------
    def ensure_valid_map(self, initial=False):
        # Generate map if initial or after level change
        if initial:
            self.game_map.generate_map()

        # Ensure at least one stairs (except on final level where we may want a boss without stairs)
        if self.game_map.current_level < MAX_LEVELS:
            has_stairs = False
            for y in range(self.game_map.height):
                for x in range(self.game_map.width):
                    if self.game_map.get_tile(x, y) == TileType.STAIRS_DOWN.value:
                        has_stairs = True
                        break
                if has_stairs:
                    break
            if not has_stairs:
                # Place stairs on a random empty tile
                empties = [(x, y) for y in range(self.game_map.height) for x in range(self.game_map.width)
                           if self.game_map.get_tile(x, y) == TileType.EMPTY.value]
                if empties:
                    sx, sy = random.choice(empties)
                    self.game_map.set_tile(sx, sy, TileType.STAIRS_DOWN.value)

        # Ensure player start on empty
        px, py = getattr(self.game_map, "player_start", (1, 1))
        if not self.game_map.is_valid_position(px, py) or self.game_map.get_tile(px, py) == TileType.WALL.value:
            # find empty
            empties = [(x, y) for y in range(self.game_map.height) for x in range(self.game_map.width)
                       if self.game_map.get_tile(x, y) == TileType.EMPTY.value]
            if empties:
                px, py = random.choice(empties)
        self.player.x, self.player.y = px, py
        self.game_map.reveal_area(self.player.x, self.player.y)

    # ---------- UI Drawing ----------
    def draw_tile(self, x: int, y: int, tile_type: str, visible: bool):
        screen_x = 50 + x * TILE_SIZE
        screen_y = 50 + y * TILE_SIZE
        if not visible:
            pygame.draw.rect(self.screen, DARK_GRAY, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(self.screen, BLACK, (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)
            return

        if tile_type == TileType.WALL.value:
            pygame.draw.rect(self.screen, BROWN, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        elif tile_type == TileType.TREASURE.value:
            self.screen.blit(self.chest_sprite, (screen_x, screen_y))
        elif tile_type == TileType.MONSTER.value:
            self.screen.blit(self.monster_sprite, (screen_x, screen_y))
        elif tile_type == TileType.STAIRS_DOWN.value:
            if self.stairs_sprite:
                self.screen.blit(self.stairs_sprite, (screen_x, screen_y))
            else:
                pygame.draw.rect(self.screen, PURPLE, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        else:  # EMPTY
            pygame.draw.rect(self.screen, LIGHT_GRAY, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

        pygame.draw.rect(self.screen, BLACK, (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)

    def draw_map(self):
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                tile_type = self.game_map.get_tile(x, y)
                visible = self.game_map.visible_map[x][y]
                self.draw_tile(x, y, tile_type, visible)
        # Draw player
        px = 50 + self.player.x * TILE_SIZE
        py = 50 + self.player.y * TILE_SIZE
        self.screen.blit(self.player_sprite, (px, py))

    def draw_ui_panel(self):
        panel_x = SCREEN_WIDTH - UI_PANEL_WIDTH
        panel_y = 0
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, UI_PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, UI_PANEL_WIDTH, SCREEN_HEIGHT), 2)

        title = self.large_font.render(f"Level {self.game_map.current_level}/{MAX_LEVELS}", True, WHITE)
        self.screen.blit(title, (panel_x + 20, 20))

        # Stats
        stats_y = 80
        if self.start_time and self.state == GameState.PLAYING:
            self.run_time = time.time() - self.start_time
        stats = [
            f"Health: {self.player.health}/{self.player.max_health}",
            f"Lvl: {self.player.level}  EXP: {self.player.experience}",
            f"Gold: {self.player.gold}",
            f"ATK: {self.player.attack}  DEF: {self.player.defense}",
            f"Time: {self.run_time:.1f}s",
        ]
        for stat in stats:
            text = self.font.render(stat, True, WHITE)
            self.screen.blit(text, (panel_x + 20, stats_y))
            stats_y += 25

        # Health bar
        health_bar_x = panel_x + 20
        health_bar_y = stats_y + 10
        health_bar_width = UI_PANEL_WIDTH - 40
        health_bar_height = 20
        pygame.draw.rect(self.screen, RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        hw = int((self.player.health / max(1, self.player.max_health)) * health_bar_width)
        pygame.draw.rect(self.screen, GREEN, (health_bar_x, health_bar_y, hw, health_bar_height))
        pygame.draw.rect(self.screen, BLACK, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)
        ht = self.font.render(f"{self.player.health}/{self.player.max_health}", True, BLACK)
        self.screen.blit(ht, ht.get_rect(center=(health_bar_x + health_bar_width//2, health_bar_y + health_bar_height//2)))

        # Messages
        message_y = health_bar_y + health_bar_height + 30
        mt = self.font.render("Messages:", True, WHITE)
        self.screen.blit(mt, (panel_x + 20, message_y))
        if self.message_log:
            messages = self.message_log[-5:]
            message_y += 30
            for i, message in enumerate(messages):
                msg = self.font.render(f"• {message}", True, LIGHT_GRAY)
                self.screen.blit(msg, (panel_x + 20, message_y + i * 22))

    def draw_buttons(self):
        for button in self.play_buttons:
            button.draw(self.screen)
        if self.quit_button:
            self.quit_button.draw(self.screen)

    def draw_inventory(self):
        if not self.show_inventory:
            return
        panel_x = SCREEN_WIDTH // 2 - 250
        panel_y = SCREEN_HEIGHT // 2 - 250
        panel_w = 500
        panel_h = 500
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        title = self.large_font.render("Inventory", True, WHITE)
        self.screen.blit(title, (panel_x + 20, panel_y + 15))
        hint = self.font.render("ESC to close • Scroll to navigate • Click item to use/sell", True, LIGHT_GRAY)
        self.screen.blit(hint, (panel_x + 20, panel_y + 55))

        # Scrollable viewport
        viewport_y = panel_y + 90
        viewport_h = panel_h - 140
        items = self.player.inventory
        start_index = max(0, self.scroll_offset // self.inventory_row_height)
        visible_rows = viewport_h // self.inventory_row_height + 1
        end_index = min(len(items), start_index + visible_rows)

        for idx in range(start_index, end_index):
            item = items[idx]
            row_y = viewport_y + (idx - start_index) * self.inventory_row_height
            row_rect = pygame.Rect(panel_x + 20, row_y, panel_w - 40, self.inventory_row_height - 8)
            pygame.draw.rect(self.screen, (80, 80, 80), row_rect, border_radius=6)
            pygame.draw.rect(self.screen, BLACK, row_rect, 1, border_radius=6)

            name = f"{item.name} ({item.item_type})"
            desc = item.description
            text1 = self.font.render(name, True, WHITE)
            text2 = self.font.render(desc, True, LIGHT_GRAY)
            self.screen.blit(text1, (row_rect.x + 10, row_rect.y + 6))
            self.screen.blit(text2, (row_rect.x + 10, row_rect.y + 30))

        # Simple scrollbar indicator
        if len(items) * self.inventory_row_height > viewport_h:
            bar_h = max(30, int(viewport_h * viewport_h / (len(items) * self.inventory_row_height)))
            max_scroll = len(items) * self.inventory_row_height - viewport_h
            bar_y = viewport_y + int((self.scroll_offset / max(1, max_scroll)) * (viewport_h - bar_h))
            pygame.draw.rect(self.screen, LIGHT_GRAY, (panel_x + panel_w - 18, bar_y, 6, bar_h), border_radius=3)

        # Equipped
        eq_y = panel_y + panel_h - 40
        eq_text = self.font.render(
            f"Equipped: Wpn={getattr(self.player.equipped_weapon,'name', 'None')}  Arm={getattr(self.player.equipped_armor,'name','None')}",
            True, WHITE
        )
        self.screen.blit(eq_text, (panel_x + 20, eq_y))

    def draw_quests(self):
        if not self.show_quests:
            return
        panel_x = SCREEN_WIDTH // 2 - 250
        panel_y = SCREEN_HEIGHT // 2 - 200
        panel_w = 500
        panel_h = 400
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)
        title = self.large_font.render("Quests", True, WHITE)
        self.screen.blit(title, (panel_x + 20, panel_y + 15))

        quests_y = panel_y + 70
        quests = self.quest_log.get_quests()
        for i, quest in enumerate(quests):
            status = "✓ Completed" if getattr(quest, "completed", False) else "○ In progress"
            qtext = f"{i+1}. {quest.title} — {status}"
            text = self.font.render(qtext, True, WHITE)
            self.screen.blit(text, (panel_x + 20, quests_y))
            desc = self.font.render(f"   {quest.description}", True, LIGHT_GRAY)
            self.screen.blit(desc, (panel_x + 20, quests_y + 22))
            reward = self.font.render(f"   Reward: {quest.reward}", True, YELLOW)
            self.screen.blit(reward, (panel_x + 20, quests_y + 42))
            quests_y += 70

    # ---------- Messages ----------
    def add_message(self, message: str):
        self.message_log.append(message)
        if len(self.message_log) > 50:
            self.message_log.pop(0)

    # ---------- Inventory Actions ----------
    def sell_treasure(self, item: Item):
        value = item.value if hasattr(item, "value") and isinstance(item.value, (int, float)) else 50
        self.player.gold += int(value)
        self.player.remove_item(item.name)
        self.add_message(f"Sold treasure '{item.name}' for {int(value)} gold!")

    def use_item_click(self, mouse_pos):
        if not self.show_inventory:
            return
        panel_x = SCREEN_WIDTH // 2 - 250
        panel_y = SCREEN_HEIGHT // 2 - 250
        panel_w = 500
        panel_h = 500
        viewport_y = panel_y + 90
        viewport_h = panel_h - 140

        if not (panel_x <= mouse_pos[0] <= panel_x + panel_w and viewport_y <= mouse_pos[1] <= viewport_y + viewport_h):
            return

        items = self.player.inventory
        if not items:
            return
        start_index = max(0, self.scroll_offset // self.inventory_row_height)
        visible_rows = viewport_h // self.inventory_row_height + 1
        end_index = min(len(items), start_index + visible_rows)

        for idx in range(start_index, end_index):
            row_y = viewport_y + (idx - start_index) * self.inventory_row_height
            row_rect = pygame.Rect(panel_x + 20, row_y, panel_w - 40, self.inventory_row_height - 8)
            if row_rect.collidepoint(mouse_pos):
                item = items[idx]
                # Treasure => sell; else call player.use_item
                if item.item_type == "treasure":
                    self.sell_treasure(item)
                else:
                    if self.player.use_item(item.name):
                        self.add_message(f"Used {item.name}!")
                    else:
                        self.add_message(f"Couldn't use {item.name}.")
                break

    # ---------- Movement / Interactions ----------
    def move_player(self, dx: int, dy: int):
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        if not self.game_map.is_valid_position(new_x, new_y):
            self.add_message("You can't move there!")
            return

        tile = self.game_map.get_tile(new_x, new_y)
        if tile == TileType.WALL.value:
            self.add_message("You can't walk through walls!")
            return
        

        self.move_stack.push((self.player.x, self.player.y))
        self.player.x = new_x
        self.player.y = new_y
        self.handle_tile_interaction(tile, new_x, new_y)
        self.game_map.reveal_area(self.player.x, self.player.y)

    def handle_tile_interaction(self, tile: str, x: int, y: int):
        if tile == TileType.TREASURE.value:
            # Choose treasure or useful item
            item_name = random.choice(list(self.items.keys()))
            item = self.items[item_name]
            self.player.add_item(item)
            self.game_map.set_tile(x, y, TileType.EMPTY.value)
            self.add_message(f"You found Treasure: {item.name}!")
            # Quest: treasure
            try:
                self.quest_log.complete_quest("treasure")
            except Exception:
                pass

        elif tile == TileType.MONSTER.value:
            # On final level, force boss
            if self.game_map.current_level >= MAX_LEVELS:
                monster = self.monsters["dragon"]
            else:
                monster_name = random.choice([m for m in self.monsters.keys() if m != "dragon"])
                monster = self.monsters[monster_name]
            self.add_message(f"A {monster.name} appears!")
            self.combat(monster)
            self.game_map.set_tile(x, y, TileType.EMPTY.value)

        elif tile == TileType.STAIRS_DOWN.value:
            if self.game_map.current_level >= MAX_LEVELS:
                # Final floor: stairs act as completion if boss is defeated or no boss present
                if self.boss_defeated:
                    self.trigger_victory()
                else:
                    self.add_message("A powerful presence blocks your path...")
            else:
                self.add_message("You descend deeper...")
                self.next_level()

    def grant_quest_rewards(self):
        """Grant rewards the moment a quest flips to completed."""
        for q in self.quest_log.get_quests():
            if getattr(q, "completed", False) and q.title not in self.rewarded_quests:
                reward_text = str(getattr(q, "reward", ""))
                # Simple parsing for gold
                if "Gold" in reward_text:
                    try:
                        amt = int(''.join(ch for ch in reward_text if ch.isdigit()))
                        self.player.gold += amt
                        self.add_message(f"Quest '{q.title}' reward: +{amt} Gold")
                    except Exception:
                        self.add_message(f"Quest '{q.title}' completed!")
                elif "weapon" in reward_text.lower():
                    self.player.add_item(self.items["steel_sword"])
                    self.add_message(f"Quest '{q.title}' reward: Steel Sword")
                elif "armor" in reward_text.lower():
                    self.player.add_item(self.items["iron_shield"])
                    self.add_message(f"Quest '{q.title}' reward: Iron Shield")
                else:
                    self.add_message(f"Quest '{q.title}' completed!")
                self.rewarded_quests.add(q.title)

    def combat(self, monster: Monster):
        # Clone monster stats so repeated encounters aren't permanently damaged
        mob = Monster(monster.name, monster.health, monster.attack, monster.defense)
        while mob.health > 0 and self.player.is_alive():
            damage = max(1, self.player.attack - mob.defense)
            mob.health -= damage
            self.add_message(f"You deal {damage} to {mob.name}.")
            if mob.health <= 0:
                self.add_message(f"You defeated {mob.name}!")
                self.player.experience += 20
                gold_gain = random.randint(10, 30)
                self.player.gold += gold_gain
                self.add_message(f"Loot: +{gold_gain} gold")
                # Quest updates
                try:
                    self.quest_log.complete_quest(mob.name.lower())
                except Exception:
                    pass
                if mob.name.lower() == "dragon":
                    self.boss_defeated = True
                break
            # Monster attacks
            mdmg = max(1, mob.attack - self.player.defense)
            self.player.take_damage(mdmg)
            self.add_message(f"{mob.name} hits you for {mdmg}.")
            if not self.player.is_alive():
                break

        if not self.player.is_alive():
            self.add_message("dead: You have fallen.")
            self.state = GameState.GAME_OVER
        else:
            self.add_message(f"Your health: {self.player.health}")
        self.grant_quest_rewards()

    def undo_move(self):
        if self.move_stack.is_empty():
            self.add_message("No moves to undo!")
            return
        last_pos = self.move_stack.pop()
        self.player.x, self.player.y = last_pos
        self.add_message(f"Undo → ({self.player.x}, {self.player.y})")
        self.game_map.reveal_area(self.player.x, self.player.y)

    def next_level(self):
        self.game_map.current_level += 1
        if self.game_map.current_level > MAX_LEVELS:
            # Safety: shouldn't happen, consider victory
            self.trigger_victory()
            return
        self.game_map.generate_map()
        self.ensure_valid_map(initial=False)
        self.add_message(f"Welcome to level {self.game_map.current_level}!")
        # On final floor, increase monster density by converting some empties to monsters visually
        if self.game_map.current_level >= MAX_LEVELS:
            self.add_message("A terrifying presence fills the air...")

    def trigger_victory(self):
        total_time = time.time() - (self.start_time or time.time())
        self.add_message(f"Dungeon Completed in {total_time:.1f}s!")
        if self.highscore is None or total_time < self.highscore:
            self.highscore = total_time
            self.save_highscore(total_time)
            self.add_message("New Highscore!")
        self.state = GameState.VICTORY

    # ---------- Event Handling ----------
    def handle_menu_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.QUIT

        for b in self.menu_buttons:
            if b.handle_event(event):
                if b.text.startswith("Start"):
                    self.start_new_run()
                elif b.text.startswith("Difficulty"):
                    self.difficulty_index = (self.difficulty_index + 1) % len(self.difficulties)
                    self.difficulty = self.difficulties[self.difficulty_index]
                    b.text = f"Difficulty: {self.difficulty.capitalize()}"
                    # Update map size scaling preview
                    self.map_size = self.get_map_size_by_difficulty()
                elif b.text == "Quit":
                    self.state = GameState.QUIT

    def start_new_run(self):
        self.boss_defeated = False
        self.rewarded_quests.clear()
        self.difficulty = self.difficulties[self.difficulty_index]
        self.map_size = self.get_map_size_by_difficulty()
        self.player = Player(1, 1)  # fresh player per your base classes
        self.game_map = GameMap(self.map_size[0], self.map_size[1], self.difficulty)
        self.quest_log = QuestLog()
        self.move_stack = MoveStack()
        self.action_queue = ActionQueue()
        self.initialize_quests()
        self.ensure_valid_map(initial=True)
        self.message_log.clear()
        self.add_message(f"Run started on '{self.difficulty.capitalize()}'!")
        self.state = GameState.PLAYING
        self.start_time = time.time()

    def handle_play_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.show_inventory or self.show_quests:
                    self.show_inventory = False
                    self.show_quests = False
                else:
                    # Pause back to menu?
                    self.state = GameState.MENU
            elif event.key in (pygame.K_w, pygame.K_UP):
                self.move_player(0, -1)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.move_player(0, 1)
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self.move_player(-1, 0)
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self.move_player(1, 0)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Click buttons
                for button in self.play_buttons:
                    if button.handle_event(event):
                        if button.text == "Inventory":
                            self.show_inventory = not self.show_inventory
                            self.show_quests = False
                        elif button.text == "Quests":
                            self.show_quests = not self.show_quests
                            self.show_inventory = False
                        elif button.text == "Undo":
                            self.undo_move()
                if self.quit_button and self.quit_button.handle_event(event):
                    self.state = GameState.MENU
                # Click inventory rows to use/sell
                self.use_item_click(event.pos)
            elif event.button == 4:  # scroll up
                self.scroll_offset = max(0, self.scroll_offset - 20)
            elif event.button == 5:  # scroll down
                # naive max based on current items
                max_scroll = max(0, len(self.player.inventory) * self.inventory_row_height - (500 - 140))
                self.scroll_offset = min(max_scroll, self.scroll_offset + 20)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = GameState.QUIT
            if self.state == GameState.MENU:
                self.handle_menu_events(event)
            elif self.state == GameState.PLAYING:
                self.handle_play_events(event)
            elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
                if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                    # Any key/click returns to menu
                    self.state = GameState.MENU

    # ---------- Screens ----------
    def draw_loading(self):
        self.screen.fill(BLACK)
        t = self.title_font.render("Loading...", True, WHITE)
        self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))

    def draw_menu(self):
        self.screen.fill((18, 18, 24))
        title = self.title_font.render("Dungeon Crawler", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 140)))

        if self.highscore is not None:
            hs = self.font.render(f"Best Time: {self.highscore:.1f}s", True, LIGHT_GRAY)
            self.screen.blit(hs, hs.get_rect(center=(SCREEN_WIDTH//2, 200)))

        for b in self.menu_buttons:
            b.draw(self.screen)

        hint = self.font.render("ESC to quit • Use mouse to select", True, LIGHT_GRAY)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 60)))

    def draw_game_over(self):
        self.screen.fill((30, 0, 0))
        t1 = self.title_font.render("dead: You have fallen.", True, RED)
        self.screen.blit(t1, t1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40)))
        t2 = self.font.render("Click or press any key to return to Main Menu", True, WHITE)
        self.screen.blit(t2, t2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20)))

    def draw_victory(self):
        self.screen.fill((0, 30, 0))
        t1 = self.title_font.render("Dungeon Completed!", True, GOLD)
        self.screen.blit(t1, t1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60)))
        t2 = self.font.render(f"Time: {self.run_time:.1f}s   Best: {self.highscore:.1f}s" if self.highscore else f"Time: {self.run_time:.1f}s",
                              True, WHITE)
        self.screen.blit(t2, t2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
        t3 = self.font.render("Click or press any key to return to Main Menu", True, WHITE)
        self.screen.blit(t3, t3.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40)))

    # ---------- Main Loop ----------
    def run(self):
        # Loading state then to menu
        while True:
            self.handle_events()
            if self.state == GameState.QUIT:
                break

            if self.state == GameState.LOADING:
                self.draw_loading()
                if time.time() - self.loading_start >= self.loading_duration:
                    self.state = GameState.MENU

            elif self.state == GameState.MENU:
                self.draw_menu()

            elif self.state == GameState.PLAYING:
                # Death check
                if not self.player.is_alive():
                    self.add_message("dead: You have been defeated.")
                    self.state = GameState.GAME_OVER

                self.screen.fill(BLACK)
                self.draw_map()
                self.draw_ui_panel()
                self.draw_buttons()

                if self.show_inventory:
                    self.draw_inventory()
                if self.show_quests:
                    self.draw_quests()

                controls_text = "WASD / Arrows: Move | I: (disabled) | Q: (disabled) | ESC: Close/Back"
                controls = self.font.render(controls_text, True, LIGHT_GRAY)
                self.screen.blit(controls, (20, SCREEN_HEIGHT - 30))

            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()

            elif self.state == GameState.VICTORY:
                self.draw_victory()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

def main():
    game = DungeonCrawlerGUI("normal")
    game.run()

if __name__ == "__main__":
    main()
