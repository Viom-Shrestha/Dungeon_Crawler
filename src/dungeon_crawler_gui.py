#Author Viom Shrestha
import pygame
import random
import time
import os
from typing import List, Tuple, Optional, Dict
from enum import Enum, auto

# Initialize Pygame
pygame.init()
pygame.mixer.init()

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

sword_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sword.mp3"))
monster_roar = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "monster_roar.mp3"))
levelup_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "levelup.mp3"))
# Import your existing classes
from dungeon_crawler import (
    TileType, Item, Monster, Quest, QuestLog, MAP_SIZES, BASE_MONSTERS,
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
        self.player = Player(1, 1, "P1")
        self.monsters = self.create_monsters()
        self.game_map = GameMap(self.map_size[0], self.map_size[1], difficulty)
        self.quest_log = QuestLog()
        self.move_stack = MoveStack()
        self.action_queue = ActionQueue()
        self.dungeon = DungeonCrawler()
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
        self.draw_funcs = {
            GameState.LOADING: self.draw_loading,
            GameState.MENU: self.draw_menu,
            GameState.PLAYING: self.draw_playing,
            GameState.GAME_OVER: self.draw_game_over,
            GameState.VICTORY: self.draw_victory,
        }

        # Pygame setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Crawler - GUI Version")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 64)

        # Sprites
        self.player_sprites = {}
        self.current_direction = "down"
        self.monster_sprite = None
        self.chest_sprite = None
        self.stairs_sprite = None

        # --- Multiplayer setup ---
        self.multiplayer = True  # set False to disable 2P
        self.player2 = Player(1, 1, "P2")
        self.player2_sprites = {}
        self.player_sprite = None
        self.player2_sprite = None

        # --- Shared inventory & active player ---
        self.player2.inventory = self.player.inventory
        self.active_player = 1  # 1 or 2 — toggled by keys 1/2
        # Friendly UI hint for inventory usage
        self.inventory_target_names = {1: "P1", 2: "P2"}


        # Monster sprites dict (used in draw & encounters)
        self.monster_sprites = {}

        self.load_sprites()

        # Monster + Items (no doors/keys now)
        self.monsters = self.create_monsters()
        self.items = self.dungeon.create_items()  # exclude keys
        self.initialize_quests()

        # UI buttons
        self.create_menu_buttons()
        self.create_play_buttons()

        # Reveal starting area & ensure valid map
        self.ensure_valid_map(initial=True)

    # ---------- Setup / Loading ----------
    def load_sprites(self):
        # Player 1 directional
        for d, color in [("up", BLUE), ("down", BLUE), ("left", BLUE), ("right", BLUE)]:
            p = os.path.join(ASSETS_DIR, f"player_{d}.png")
            self.player_sprites[d] = pygame.transform.scale(
                safe_load_sprite(p, color), (TILE_SIZE, TILE_SIZE)
            )
        # Fallback from player.png if any missing
        fallback = pygame.transform.scale(
            safe_load_sprite(os.path.join(ASSETS_DIR, "player.png"), BLUE),
            (TILE_SIZE, TILE_SIZE),
        )
        for d in ["up", "down", "left", "right"]:
            if not self.player_sprites.get(d):
                self.player_sprites[d] = fallback
        self.player_sprite = self.player_sprites["down"]

        # Player 2 directional (cyan-ish fallback)
        if self.multiplayer:
            for d, color in [("up", (0, 220, 200)), ("down", (0, 220, 200)),
                            ("left", (0, 220, 200)), ("right", (0, 220, 200))]:
                p2 = os.path.join(ASSETS_DIR, f"player2_{d}.png")
                self.player2_sprites[d] = pygame.transform.scale(
                    safe_load_sprite(p2, color), (TILE_SIZE, TILE_SIZE)
                )
            # Fallback from player2.png if any missing
            fallback2 = pygame.transform.scale(
                safe_load_sprite(os.path.join(ASSETS_DIR, "player2.png"), (0, 220, 200)),
                (TILE_SIZE, TILE_SIZE),
            )
            for d in ["up", "down", "left", "right"]:
                if not self.player2_sprites.get(d):
                    self.player2_sprites[d] = fallback2
            self.player2_sprite = self.player2_sprites["down"]

        # Monster sprites dictionary
        self.monster_sprites = {}
        # Monsters (per-species)

        for name, monster in self.monsters.items():
            if getattr(monster, "sprite", None):
                sprite_path = os.path.join(ASSETS_DIR, monster.sprite)
                surface = safe_load_sprite(sprite_path, RED)
                if surface is None:  # file not found or load failed
                    surface = self.monster_sprite
            else:
                surface = self.monster_sprite

            self.monster_sprites[name] = pygame.transform.scale(surface, (TILE_SIZE, TILE_SIZE))
        # Tiles
        self.chest_sprite = pygame.transform.scale(
            safe_load_sprite(os.path.join(ASSETS_DIR, "chest.png"), YELLOW),
            (TILE_SIZE, TILE_SIZE),
        )
        self.stairs_sprite = pygame.transform.scale(
            safe_load_sprite(os.path.join(ASSETS_DIR, "stairs.png"), PURPLE),
            (TILE_SIZE, TILE_SIZE),
        )

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
        return MAP_SIZES.get(self.difficulty, MAP_SIZES["normal"])

    def create_monsters(self) -> Dict[str, Monster]:
        scale_factor = 1.0
        if self.difficulty == "easy":
            scale_factor = 0.7
        elif self.difficulty == "hard":
            scale_factor = 1.5

        monsters: Dict[str, Monster] = {}
        for name, stats in BASE_MONSTERS.items():
            scaled_health = int(stats["health"] * scale_factor)
            scaled_attack = int(stats["attack"] * scale_factor)
            scaled_defense = int(stats["defense"] * scale_factor)

            m = Monster(name.capitalize(), scaled_health, scaled_attack, scaled_defense)
            # keep rewards + sprite on the instance
            setattr(m, "exp", stats.get("exp", 20))
            setattr(m, "gold", stats.get("gold", 10))
            setattr(m, "sprite", stats.get("sprite", None))  # <-- THIS LINE IS CRUCIAL
            monsters[name] = m

        return monsters

    def initialize_quests(self):
        for quest in DungeonCrawler.get_default_quests():
            self.quest_log.add_quest(quest)

    def create_menu_buttons(self):
        cx = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - 40
        self.menu_buttons = [
            Button(cx - 120, start_y - 120, 240, 50, "Start Game", GREEN, (0, 200, 0), 36),
            Button(cx - 120, start_y - 40, 240, 50, f"Difficulty: {self.difficulties[self.difficulty_index].capitalize()}", BLUE, (0, 0, 200), 32),
            Button(cx - 120, start_y + 40, 240, 50, f"Multiplayer: {'On' if self.multiplayer else 'Off'}", ORANGE, (200, 120, 0), 32),
            Button(cx - 120, start_y + 120, 240, 50, "Quit", RED, (200, 0, 0), 36),
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

        # --- Place Player 2 on an empty nearby tile (not same as P1) ---
        if self.multiplayer:
            p1x, p1y = self.player.x, self.player.y
            placed = False
            # Try immediate neighbors first, then any empty
            neighbors = [(p1x+1,p1y),(p1x-1,p1y),(p1x,p1y+1),(p1x,p1y-1)]
            for nx, ny in neighbors:
                if 0 <= nx < self.game_map.width and 0 <= ny < self.game_map.height:
                    if self.game_map.get_tile(nx, ny) == TileType.EMPTY.value:
                        self.player2.x, self.player2.y = nx, ny
                        placed = True
                        break
            if not placed:
                empties = [(x, y) for y in range(self.game_map.height) for x in range(self.game_map.width)
                        if self.game_map.get_tile(x, y) == TileType.EMPTY.value and (x, y) != (p1x, p1y)]
                if empties:
                    self.player2.x, self.player2.y = random.choice(empties)
            self.game_map.reveal_area(self.player2.x, self.player2.y)
        # ---------------------------------------------    
        # Ensure stairs are not completely surrounded by walls
        sx, sy = None, None
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                if self.game_map.get_tile(x, y) == TileType.STAIRS_DOWN.value:
                    sx, sy = x, y
                    break
            if sx is not None: break

        if sx is not None:
            neighbors = [(sx+1,sy),(sx-1,sy),(sx,sy+1),(sx,sy-1)]
            for nx, ny in neighbors:
                if 0 <= nx < self.game_map.width and 0 <= ny < self.game_map.height:
                    if self.game_map.get_tile(nx, ny) == TileType.WALL.value:
                        self.game_map.set_tile(nx, ny, TileType.EMPTY.value)
        
        if self.game_map.current_level == MAX_LEVELS:
            # Place dragon on a random empty tile
            empties = [(x, y) for y in range(self.game_map.height) for x in range(self.game_map.width)
                    if self.game_map.get_tile(x, y) == TileType.EMPTY.value]
            if empties:
                dx, dy = random.choice(empties)
                self.game_map.set_tile(dx, dy, f"{TileType.MONSTER.value}:dragon")


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

        elif tile_type.startswith(TileType.MONSTER.value):
            parts = tile_type.split(":")
            if len(parts) > 1:
                monster_name = parts[1]
            else:
                # Assign a random monster subtype the first time
                pool = [k for k in self.monsters.keys() if k != "dragon"]
                monster_name = random.choice(pool)
                # Save it back into the map so it persists
                self.game_map.set_tile(x, y, f"{TileType.MONSTER.value}:{monster_name}")

            sprite = self.monster_sprites.get(monster_name, self.monster_sprite)
            self.screen.blit(sprite, (screen_x, screen_y))


        elif tile_type == TileType.STAIRS_DOWN.value:
            if self.stairs_sprite:
                self.screen.blit(self.stairs_sprite, (screen_x, screen_y))
            else:
                pygame.draw.rect(self.screen, PURPLE, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        else:  # EMPTY
            pygame.draw.rect(self.screen, LIGHT_GRAY, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

        pygame.draw.rect(self.screen, BLACK, (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)
        
    def draw_actor(self, actor, sprite):
        ax = 50 + actor.x * TILE_SIZE
        ay = 50 + actor.y * TILE_SIZE
        self.screen.blit(sprite, (ax, ay))

    def draw_map(self):
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                tile_type = self.game_map.get_tile(x, y)
                visible = self.game_map.visible_map[y][x]
                self.draw_tile(x, y, tile_type, visible)
        # Draw player
        self.draw_actor(self.player, self.player_sprite)
        if self.multiplayer:
            self.draw_actor(self.player2, self.player2_sprite)

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
        # ... existing stats list ...
        stats = [
            f"Health: {self.player.health}/{self.player.max_health}",
            f"Lvl: {self.player.level}  EXP: {self.player.experience}",
            f"Gold: {self.player.gold}",
            f"ATK: {self.player.attack}  DEF: {self.player.defense}",
            f"Time: {self.run_time:.1f}s",
        ]
        if self.multiplayer:
            stats += [
                f"P2 Health: {self.player2.health}/{self.player2.max_health}",
                f"P2 Lvl: {self.player2.level}  EXP: {self.player2.experience}",
                f"P2 ATK: {self.player2.attack}  DEF: {self.player2.defense}",
            ]
        

        for stat in stats:
            text = self.font.render(stat, True, WHITE)
            self.screen.blit(text, (panel_x + 20, stats_y))
            stats_y += 25

        # Health bars area (P1)
        health_bar_x = panel_x + 20
        health_bar_y = stats_y + 10
        health_bar_width = UI_PANEL_WIDTH - 40
        health_bar_height = 18

        # P1 bar
        pygame.draw.rect(self.screen, RED, (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        hw1 = int((self.player.health / max(1, self.player.max_health)) * health_bar_width)
        pygame.draw.rect(self.screen, GREEN, (health_bar_x, health_bar_y, hw1, health_bar_height))
        pygame.draw.rect(self.screen, BLACK, (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2)
        ht1 = self.font.render(f"P1 {self.player.health}/{self.player.max_health}", True, BLACK)
        self.screen.blit(ht1, (health_bar_x + 6, health_bar_y + 1))

        # P2 bar (if present)
        if self.multiplayer:
            health_bar_y2 = health_bar_y + health_bar_height + 8
            pygame.draw.rect(self.screen, RED, (health_bar_x, health_bar_y2, health_bar_width, health_bar_height))
            hw2 = int((self.player2.health / max(1, self.player2.max_health)) * health_bar_width)
            pygame.draw.rect(self.screen, GREEN, (health_bar_x, health_bar_y2, hw2, health_bar_height))
            pygame.draw.rect(self.screen, BLACK, (health_bar_x, health_bar_y2, health_bar_width, health_bar_height), 2)
            ht2 = self.font.render(f"P2 {self.player2.health}/{self.player2.max_health}", True, BLACK)
            self.screen.blit(ht2, (health_bar_x + 6, health_bar_y2 + 1))
            # push the messages block down for spacing
            message_y = health_bar_y2 + health_bar_height + 22
        else:
            message_y = health_bar_y + health_bar_height + 30

        # Messages
        message_y = health_bar_y + health_bar_height + 30
        mt = self.font.render("Messages:", True, WHITE)
        self.screen.blit(mt, (panel_x + 20, message_y))
        if self.message_log:
            messages = self.message_log[-5:]
            message_y += 30
            for message in messages:
                words = message.split(" ")
                current_line = ""
                for word in words:
                    test_line = current_line + word + " "
                    if self.font.size(test_line)[0] > UI_PANEL_WIDTH - 40:
                        line_surface = self.font.render(f"• {current_line.strip()}", True, LIGHT_GRAY)
                        self.screen.blit(line_surface, (panel_x + 20, message_y))
                        message_y += self.font.get_height() + 2
                        current_line = word + " "
                    else:
                        current_line = test_line
                if current_line:
                    line_surface = self.font.render(f"• {current_line.strip()}", True, LIGHT_GRAY)
                    self.screen.blit(line_surface, (panel_x + 20, message_y))
                    message_y += self.font.get_height() + 2

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
        panel_h = 550

        # Panel background
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        # Title
        title = self.large_font.render("Inventory", True, WHITE)
        self.screen.blit(title, (panel_x + 20, panel_y + 15))

        # Hints
        hint1 = self.font.render("ESC to close • Scroll to navigate", True, LIGHT_GRAY)
        hint2 = self.font.render("Left click = equip/use • Right click = sell", True, LIGHT_GRAY)
        self.screen.blit(hint1, (panel_x + 20, panel_y + 50))
        self.screen.blit(hint2, (panel_x + 20, panel_y + 70))

        # Active player target indicator
        target_label = f"Active target: {self.inventory_target_names[self.active_player]} (Press 1/2 to switch)"
        self.screen.blit(self.font.render(target_label, True, YELLOW), (panel_x + 20, panel_y + 90))

        # --- Equipped items block ---
        eq_y = panel_y + 125
        p1_weapon = self.player.equipped_weapon.name if self.player.equipped_weapon else "None"
        p1_armor = self.player.equipped_armor.name if self.player.equipped_armor else "None"
        self.screen.blit(self.font.render(f"P1 Weapon: {p1_weapon}", True, WHITE), (panel_x + 20, eq_y))
        self.screen.blit(self.font.render(f"P1 Armor:  {p1_armor}", True, WHITE), (panel_x + 20, eq_y + 20))

        if self.multiplayer:
            p2_weapon = self.player2.equipped_weapon.name if self.player2.equipped_weapon else "None"
            p2_armor = self.player2.equipped_armor.name if self.player2.equipped_armor else "None"
            self.screen.blit(self.font.render(f"P2 Weapon: {p2_weapon}", True, WHITE), (panel_x + 260, eq_y))
            self.screen.blit(self.font.render(f"P2 Armor:  {p2_armor}", True, WHITE), (panel_x + 260, eq_y + 20))

        # --- Scrollable inventory list below equipped block ---
        viewport_y = eq_y + 70
        viewport_h = panel_h - (viewport_y - panel_y) - 40  # leave some bottom padding
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
            # inside the for-loop when building desc:
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

        # Scrollbar indicator
        if len(items) * self.inventory_row_height > viewport_h:
            bar_h = max(30, int(viewport_h * viewport_h / (len(items) * self.inventory_row_height)))
            max_scroll = len(items) * self.inventory_row_height - viewport_h
            bar_y = viewport_y + int((self.scroll_offset / max(1, max_scroll)) * (viewport_h - bar_h))
            pygame.draw.rect(self.screen, LIGHT_GRAY, (panel_x + panel_w - 18, bar_y, 6, bar_h), border_radius=3)


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

    def use_item_click(self, mouse_pos, button: int):
        if not self.show_inventory:
            return
        panel_x = SCREEN_WIDTH // 2 - 250
        panel_y = SCREEN_HEIGHT // 2 - 250
        panel_w = 500
        panel_h = 500
        eq_y = panel_y + 125
        viewport_y = eq_y + 70
        viewport_h = panel_h - (viewport_y - panel_y) - 40

        if not (panel_x <= mouse_pos[0] <= panel_x + panel_w and
            viewport_y <= mouse_pos[1] <= viewport_y + viewport_h):
            return

        items = self.player.inventory  # shared
        if not items:
            return
        start_index = max(0, self.scroll_offset // self.inventory_row_height)
        visible_rows = viewport_h // self.inventory_row_height + 1
        end_index = min(len(items), start_index + visible_rows)

        # resolve the active Player object
        target = self.player if self.active_player == 1 else self.player2

        for idx in range(start_index, end_index):
            row_y = viewport_y + (idx - start_index) * self.inventory_row_height
            row_rect = pygame.Rect(panel_x + 20, row_y, panel_w - 40, self.inventory_row_height - 8)
            if row_rect.collidepoint(mouse_pos):
                item = items[idx]

                # if target is dead, disallow using/equipping on them
                if not getattr(target, "is_alive", lambda: True)():
                    self.add_message(f"Cannot use or equip items on {self.inventory_target_names[self.active_player]} — they are dead.")
                    return

                if button == 1:  # left click
                    msg = item.use(target)
                    self.add_message(msg)
                elif button == 3:  # right click
                    msg = item.sell(target)
                    self.add_message(msg)
                break

    def check_level_up(self, actor: Player):
        exp_needed = 50 + (actor.level * 10)
        if actor.experience >= exp_needed:
            actor.level += 1
            actor.experience -= exp_needed
            actor.max_health += 10
            actor.base_attack += 2
            actor.base_defense += 2
            print(f"LEVEL UP! You are now level {actor.level}!")
            self.add_message(f"{'P1' if actor is self.player else 'P2'} leveled up to {actor.level}!")
            # Heal a bit on level up    
            actor.health = self.player.max_health

    def move_actor(self, actor: Player, sprite_set: Dict[str, pygame.Surface], dx: int, dy: int):
        if not actor.is_alive():
            self.add_message(f"{'P1' if actor is self.player else 'P2'} is dead and cannot move.")
            return
        if dx == 1:   sprite = sprite_set["right"]
        elif dx == -1: sprite = sprite_set["left"]
        elif dy == -1: sprite = sprite_set["up"]
        else:          sprite = sprite_set["down"]

        if actor is self.player:
            self.player_sprite = sprite
        else:
            self.player2_sprite = sprite

        new_x, new_y = actor.x + dx, actor.y + dy
        if not self.game_map.is_valid_position(new_x, new_y):
            self.add_message("You can't move there!")
            return

        tile = self.game_map.get_tile(new_x, new_y)
        if tile == TileType.WALL.value:
            self.add_message("You can't walk through walls!")
            return

        self.move_stack.push((actor.x, actor.y))
        actor.x, actor.y = new_x, new_y
        self.handle_tile_interaction(actor, tile, new_x, new_y)
        self.game_map.reveal_area(actor.x, actor.y)

    def handle_tile_interaction(self, actor: Player, tile: str, x: int, y: int):
        if tile == TileType.TREASURE.value:
            item_name = random.choice(list(self.items.keys()))
            item = self.items[item_name]
            actor.add_item(item)
            self.game_map.set_tile(x, y, TileType.EMPTY.value)
            self.add_message(f"You found Treasure: {item.name}!")
            try:
                quest = self.quest_log.complete_quest("treasure")
                if quest:
                    self.grant_quest_rewards()
            except Exception:
                pass

        elif tile.startswith(TileType.MONSTER.value):
            parts = tile.split(":")
            if len(parts) > 1 and parts[1] in self.monsters:
                monster_name = parts[1]
            else:
                pool = [k for k in self.monsters.keys() if k != "dragon"] or list(self.monsters.keys())
                monster_name = random.choice(pool)
            monster = self.monsters[monster_name]

            monster_roar.play()
            self.add_message(f"A {monster.name} appears!")
            self.combat(actor, monster)
            self.check_level_up(actor)
            self.game_map.set_tile(x, y, TileType.EMPTY.value)

        elif tile == TileType.STAIRS_DOWN.value:
            if self.game_map.current_level >= MAX_LEVELS:
                if self.boss_defeated:
                    self.trigger_victory()
                else:
                    self.add_message("A powerful presence blocks your path...")
            else:
                self.add_message("You descend deeper...")
                self.next_level()

    def grant_quest_rewards(self):
        for q in self.quest_log.get_quests():
            if getattr(q, "completed", False) and q.title not in self.rewarded_quests:
                reward = q.reward
                if isinstance(reward, dict):
                    if "gold" in reward:
                        self.player.gold += reward["gold"]
                        self.add_message(f"Quest '{q.title}' reward: +{reward['gold']} Gold")
                    if "exp" in reward:
                        self.player.experience += reward["exp"]
                        self.add_message(f"Quest '{q.title}' reward: +{reward['exp']} EXP")
                    if "item" in reward and reward["item"] in self.items:
                        self.player.add_item(self.items[reward["item"]])
                        self.add_message(f"Quest '{q.title}' reward: {self.items[reward['item']].name}")
                self.rewarded_quests.add(q.title)

    def combat(self, actor: Player, monster: Monster):
        mob = Monster(monster.name, monster.health, monster.attack, monster.defense)
        setattr(mob, "exp", getattr(monster, "exp", 20))
        setattr(mob, "gold", getattr(monster, "gold", random.randint(10, 30)))

        sword_sound.play()
        while mob.health > 0 and actor.is_alive():
            damage = max(1, actor.attack - mob.defense)
            mob.health -= damage
            self.add_message(f"You deal {damage} to {mob.name}.")
            if mob.health <= 0:
                self.add_message(f"You defeated {mob.name}!")
                # Give attacher the monster-specific reward values if they exist
                exp_gain = getattr(mob, "exp", 20)
                gold_gain = getattr(mob, "gold", random.randint(10, 30))
                actor.experience += exp_gain
                actor.gold += gold_gain
                self.add_message(f"Rewards: +{exp_gain} EXP, +{gold_gain} Gold")
                self.add_message(f"Loot: +{gold_gain} gold")

                try:
                    quest = self.quest_log.complete_quest(mob.name.lower())
                    if quest:
                        self.grant_quest_rewards()
                except Exception:
                    pass
                if mob.name.lower() == "dragon":
                    self.boss_defeated = True
                break

            # Monster attacks
            mdmg = max(1, mob.attack - actor.defense)
            actor.take_damage(mdmg)
            self.add_message(f"{mob.name} hits you for {mdmg}.")
            if not actor.is_alive():
                break

        # End-of-combat: only set GAME_OVER if both players are dead (coop)
            if not self.player.is_alive() and (not self.multiplayer or not (self.player2 and self.player2.is_alive())):
                self.add_message("dead: Both adventurers have fallen.")
                self.state = GameState.GAME_OVER
            else:
                # If the actor that fought is dead, print dead message for them but allow P2 to continue moving
                if not actor.is_alive():
                    self.add_message(f"{'P1' if actor is self.player else 'P2'} has fallen and cannot use items or equip gear.")
                else:
                    self.add_message(f"{'P1' if actor is self.player else 'P2'} health: {actor.health}")

            self.check_level_up(actor)
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
                elif b.text.startswith("Multiplayer"):
                    self.multiplayer = not self.multiplayer
                    b.text = f"Multiplayer: {'On' if self.multiplayer else 'Off'}"
                elif b.text == "Quit":
                    self.state = GameState.QUIT

    def start_new_run(self):
        self.boss_defeated = False
        self.rewarded_quests.clear()
        self.difficulty = self.difficulties[self.difficulty_index]
        self.map_size = self.get_map_size_by_difficulty()

        self.player = Player(1, 1, name="P1")  # fresh player
        self.player.inventory = []
        self.player.equipped_weapon = None
        self.player.equipped_armor = None

        if self.multiplayer:
            self.player2 = Player(1, 1, name="P2")  # recreate P2 properly
            self.player2.inventory = self.player.inventory
            self.player2.equipped_weapon = None
            self.player2.equipped_armor = None

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

        # --- BGM ---
        try:
            pygame.mixer.music.load(os.path.join(ASSETS_DIR, "bg.mp3")) 
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # loop forever
        except Exception:
            pass


    def handle_play_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.show_inventory or self.show_quests:
                    self.show_inventory = False
                    self.show_quests = False
                else:
                    self.state = GameState.MENU

            # Player 1 (WASD)
            elif event.key == pygame.K_w:
                self.move_actor(self.player, self.player_sprites, 0, -1)
            elif event.key == pygame.K_s:
                self.move_actor(self.player, self.player_sprites, 0, 1)
            elif event.key == pygame.K_a:
                self.move_actor(self.player, self.player_sprites, -1, 0)
            elif event.key == pygame.K_d:
                self.move_actor(self.player, self.player_sprites, 1, 0)

            # Player 2 (Arrows)
            elif self.multiplayer and event.key == pygame.K_UP:
                self.move_actor(self.player2, self.player2_sprites, 0, -1)
            elif self.multiplayer and event.key == pygame.K_DOWN:
                self.move_actor(self.player2, self.player2_sprites, 0, 1)
            elif self.multiplayer and event.key == pygame.K_LEFT:
                self.move_actor(self.player2, self.player2_sprites, -1, 0)
            elif self.multiplayer and event.key == pygame.K_RIGHT:
                self.move_actor(self.player2, self.player2_sprites, 1, 0)

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
                    self.start_new_run()
                    self.state = GameState.MENU
                # Click inventory rows to use/sell (pass button=1)
                self.use_item_click(event.pos, button=1)
            elif event.button == 3:
                # Right click: equip / assign to active player (pass button=3)
                self.use_item_click(event.pos, button=3)
            elif event.button == 4:  # scroll up
                self.scroll_offset = max(0, self.scroll_offset - 20)
            elif event.button == 5:  # scroll down
                max_scroll = max(0, len(self.player.inventory) * self.inventory_row_height - (500 - 140))
                self.scroll_offset = min(max_scroll, self.scroll_offset + 20)

        # Keyboard: toggle active player with 1 or 2
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.active_player = 1
                self.add_message("Active inventory target: P1")
            elif event.key == pygame.K_2 and self.multiplayer:
                self.active_player = 2
                self.add_message("Active inventory target: P2")


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

    def draw_playing(self):
        if not self.player.is_alive() and self.player2 and not self.player2.is_alive():
            self.add_message("dead: You have been defeated.")
            self.state = GameState.GAME_OVER
            return

        self.screen.fill(BLACK)
        self.draw_map()
        self.draw_ui_panel()
        self.draw_buttons()

        if self.show_inventory:
            self.draw_inventory()
        if self.show_quests:
            self.draw_quests()

        controls_text = "WASD / Arrows: Move | ESC: Close/Back"
        controls = self.font.render(controls_text, True, LIGHT_GRAY)
        self.screen.blit(controls, (20, SCREEN_HEIGHT - 30))

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
                if not self.player.is_alive() and (not self.multiplayer or not self.player2.is_alive()):
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
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        pygame.quit()

def main():
    game = DungeonCrawlerGUI("normal")
    game.run()

if __name__ == "__main__":
    main()
