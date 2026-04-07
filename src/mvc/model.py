import os
import random
import time
from typing import Dict, List, Optional, Set, Tuple

import pygame

from game_engine import (
    ActionQueue,
    BASE_MONSTERS,
    DungeonCrawler,
    GameMap,
    Item,
    MAP_SIZES,
    Monster,
    MoveStack,
    Player,
    QuestLog,
    TileType,
)
from mvc.constants import ASSETS_DIR, HIGHSCORE_FILE, MAX_LEVELS, GameState


def _safe_load_sound(filename: str) -> Optional[pygame.mixer.Sound]:
    try:
        return pygame.mixer.Sound(os.path.join(ASSETS_DIR, filename))
    except Exception:
        return None


def _safe_play(sound: Optional[pygame.mixer.Sound]) -> None:
    if sound is None:
        return
    try:
        sound.play()
    except Exception:
        pass


class GameModel:
    """Model layer: owns game state and all gameplay rules."""

    def __init__(self, difficulty: str = "normal"):
        self.difficulties = ["easy", "normal", "hard"]
        self.difficulty = difficulty if difficulty in self.difficulties else "normal"
        self.difficulty_index = self.difficulties.index(self.difficulty)

        self.map_size = self.get_map_size_by_difficulty()
        self.state = GameState.LOADING
        self.loading_start = time.time()
        self.loading_duration = 1.5

        # Core runtime entities
        self.player = Player(1, 1, "P1")
        self.player2 = Player(1, 1, "P2")
        self.multiplayer = True
        self.player2.inventory = self.player.inventory
        self.active_player = 1
        self.inventory_target_names = {1: "P1", 2: "P2"}

        self.game_map = GameMap(self.map_size[0], self.map_size[1], self.difficulty)
        self.quest_log = QuestLog()
        self.move_stack = MoveStack()
        self.action_queue = ActionQueue()
        self.dungeon = DungeonCrawler(self.difficulty)
        self.monsters = self.create_monsters()
        self.items = self.dungeon.create_items()

        # UI-facing state
        self.message_log: List[str] = []
        self.scroll_offset = 0
        self.inventory_row_height = 64
        self.show_inventory = False
        self.show_quests = False

        # Progression/session state
        self.start_time: Optional[float] = None
        self.run_time = 0.0
        self.highscore = self.load_highscore()
        self.rewarded_quests: Set[str] = set()
        self.boss_defeated = False

        # Audio
        self.sword_sound = _safe_load_sound("sword.mp3")
        self.monster_roar = _safe_load_sound("monster_roar.mp3")
        self.levelup_sound = _safe_load_sound("levelup.mp3")
        self.chest_sound = _safe_load_sound("chest.mp3")

        self.initialize_quests()
        self.ensure_valid_map(initial=True)

    # ---------- Setup ----------
    def get_map_size_by_difficulty(self) -> Tuple[int, int]:
        return MAP_SIZES.get(self.difficulty, MAP_SIZES["normal"])

    def create_monsters(self) -> Dict[str, Monster]:
        scale_factor = {"easy": 0.7, "hard": 1.5}.get(self.difficulty, 1.0)
        monsters: Dict[str, Monster] = {}
        for name, stats in BASE_MONSTERS.items():
            m = Monster(
                name.capitalize(),
                int(stats["health"] * scale_factor),
                int(stats["attack"] * scale_factor),
                int(stats["defense"] * scale_factor),
            )
            setattr(m, "exp", stats.get("exp", 20))
            setattr(m, "gold", stats.get("gold", 10))
            setattr(m, "sprite", stats.get("sprite", None))
            monsters[name] = m
        return monsters

    def initialize_quests(self) -> None:
        self.quest_log = QuestLog()
        for quest in DungeonCrawler.get_default_quests():
            self.quest_log.add_quest(quest)

    def load_highscore(self) -> Optional[float]:
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, "r", encoding="utf-8") as handle:
                    return float(handle.read().strip())
        except Exception:
            pass
        return None

    def save_highscore(self, seconds: float) -> None:
        try:
            with open(HIGHSCORE_FILE, "w", encoding="utf-8") as handle:
                handle.write(str(seconds))
        except Exception:
            pass

    def ensure_valid_map(self, initial: bool = False) -> None:
        if initial:
            self.game_map.generate_map()

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
                empties = [
                    (x, y)
                    for y in range(self.game_map.height)
                    for x in range(self.game_map.width)
                    if self.game_map.get_tile(x, y) == TileType.EMPTY.value
                ]
                if empties:
                    sx, sy = random.choice(empties)
                    self.game_map.set_tile(sx, sy, TileType.STAIRS_DOWN.value)

        px, py = getattr(self.game_map, "player_start", (1, 1))
        if not self.game_map.is_valid_position(px, py) or self.game_map.get_tile(px, py) == TileType.WALL.value:
            empties = [
                (x, y)
                for y in range(self.game_map.height)
                for x in range(self.game_map.width)
                if self.game_map.get_tile(x, y) == TileType.EMPTY.value
            ]
            if empties:
                px, py = random.choice(empties)

        self.player.x, self.player.y = px, py
        self.game_map.reveal_area(self.player.x, self.player.y)

        if self.game_map.current_level == MAX_LEVELS:
            empties = [
                (x, y)
                for y in range(self.game_map.height)
                for x in range(self.game_map.width)
                if self.game_map.get_tile(x, y) == TileType.EMPTY.value
            ]
            if empties:
                dx, dy = random.choice(empties)
                self.game_map.set_tile(dx, dy, f"{TileType.MONSTER.value}:dragon")

        if self.multiplayer:
            p1x, p1y = self.player.x, self.player.y
            placed = False
            neighbors = [(p1x + 1, p1y), (p1x - 1, p1y), (p1x, p1y + 1), (p1x, p1y - 1)]
            for nx, ny in neighbors:
                if 0 <= nx < self.game_map.width and 0 <= ny < self.game_map.height:
                    if self.game_map.get_tile(nx, ny) == TileType.EMPTY.value:
                        self.player2.x, self.player2.y = nx, ny
                        placed = True
                        break
            if not placed:
                empties = [
                    (x, y)
                    for y in range(self.game_map.height)
                    for x in range(self.game_map.width)
                    if self.game_map.get_tile(x, y) == TileType.EMPTY.value and (x, y) != (p1x, p1y)
                ]
                if empties:
                    self.player2.x, self.player2.y = random.choice(empties)
            self.game_map.reveal_area(self.player2.x, self.player2.y)

        sx, sy = None, None
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                if self.game_map.get_tile(x, y) == TileType.STAIRS_DOWN.value:
                    sx, sy = x, y
                    break
            if sx is not None:
                break

        if sx is not None:
            neighbors = [(sx + 1, sy), (sx - 1, sy), (sx, sy + 1), (sx, sy - 1)]
            for nx, ny in neighbors:
                if 0 <= nx < self.game_map.width and 0 <= ny < self.game_map.height:
                    if self.game_map.get_tile(nx, ny) == TileType.WALL.value:
                        self.game_map.set_tile(nx, ny, TileType.EMPTY.value)

    # ---------- Session / Flow ----------
    def add_message(self, message: str) -> None:
        self.message_log.append(message)
        if len(self.message_log) > 50:
            self.message_log.pop(0)

    def cycle_difficulty(self) -> str:
        self.difficulty_index = (self.difficulty_index + 1) % len(self.difficulties)
        self.difficulty = self.difficulties[self.difficulty_index]
        self.map_size = self.get_map_size_by_difficulty()
        return self.difficulty

    def set_multiplayer(self, enabled: bool) -> None:
        self.multiplayer = enabled

    def set_active_player(self, player_index: int) -> None:
        if player_index == 1:
            self.active_player = 1
            self.add_message("Active inventory target: P1")
        elif player_index == 2 and self.multiplayer:
            self.active_player = 2
            self.add_message("Active inventory target: P2")

    def get_inventory_target(self) -> Player:
        return self.player if self.active_player == 1 else self.player2

    def play_background_music(self) -> None:
        try:
            pygame.mixer.music.load(os.path.join(ASSETS_DIR, "bg.mp3"))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def start_new_run(self) -> None:
        self.boss_defeated = False
        self.rewarded_quests.clear()
        self.map_size = self.get_map_size_by_difficulty()
        self.dungeon = DungeonCrawler(self.difficulty)
        self.monsters = self.create_monsters()
        self.items = self.dungeon.create_items()

        self.player = Player(1, 1, name="P1")
        self.player.inventory = []
        self.player.equipped_weapon = None
        self.player.equipped_armor = None

        self.player2 = Player(1, 1, name="P2")
        self.player2.inventory = self.player.inventory
        self.player2.equipped_weapon = None
        self.player2.equipped_armor = None

        self.game_map = GameMap(self.map_size[0], self.map_size[1], self.difficulty)
        self.move_stack = MoveStack()
        self.action_queue = ActionQueue()
        self.initialize_quests()
        self.ensure_valid_map(initial=True)

        self.show_inventory = False
        self.show_quests = False
        self.scroll_offset = 0
        self.active_player = 1
        self.message_log.clear()
        self.add_message(f"Run started on '{self.difficulty.capitalize()}'!")

        self.state = GameState.PLAYING
        self.start_time = time.time()
        self.play_background_music()

    # ---------- Gameplay ----------
    def check_level_up(self, actor: Player) -> None:
        exp_needed = 50 + (actor.level * 10)
        if actor.experience >= exp_needed:
            actor.level += 1
            actor.experience -= exp_needed
            actor.max_health += 10
            actor.base_attack += 2
            actor.base_defense += 2
            actor.health = actor.max_health
            _safe_play(self.levelup_sound)
            self.add_message(f"{'P1' if actor is self.player else 'P2'} leveled up to {actor.level}!")

    def move_actor(self, actor: Player, dx: int, dy: int) -> None:
        if not actor.is_alive():
            self.add_message(f"{'P1' if actor is self.player else 'P2'} is dead and cannot move.")
            return

        new_x, new_y = actor.x + dx, actor.y + dy
        if not self.game_map.is_valid_position(new_x, new_y):
            self.add_message("You cannot move there.")
            return

        tile = self.game_map.get_tile(new_x, new_y)
        if tile == TileType.WALL.value:
            self.add_message("You cannot walk through walls.")
            return

        self.move_stack.push((actor.x, actor.y))
        actor.x, actor.y = new_x, new_y
        self.handle_tile_interaction(actor, tile, new_x, new_y)
        self.game_map.reveal_area(actor.x, actor.y)

    def handle_tile_interaction(self, actor: Player, tile: str, x: int, y: int) -> None:
        if tile == TileType.TREASURE.value:
            item_name = random.choice(list(self.items.keys()))
            actor.add_item(self.items[item_name])
            self.game_map.set_tile(x, y, TileType.EMPTY.value)
            self.add_message(f"You found treasure: {self.items[item_name].name}.")
            _safe_play(self.chest_sound)
            if self.quest_log.complete_quest("treasure"):
                self.grant_quest_rewards()
            return

        if tile.startswith(TileType.MONSTER.value):
            parts = tile.split(":")
            if len(parts) > 1 and parts[1] in self.monsters:
                monster_name = parts[1]
            else:
                pool = [k for k in self.monsters.keys() if k != "dragon"] or list(self.monsters.keys())
                monster_name = random.choice(pool)

            base = self.monsters[monster_name]
            monster = Monster(
                base.name,
                base.max_health,
                base.attack,
                base.defense,
                getattr(base, "sprite", None),
            )
            setattr(monster, "exp", getattr(base, "exp", 20))
            setattr(monster, "gold", getattr(base, "gold", random.randint(10, 30)))

            _safe_play(self.monster_roar)
            self.add_message(f"A {monster.name} appears!")
            self.combat(actor, monster)
            self.check_level_up(actor)
            self.game_map.set_tile(x, y, TileType.EMPTY.value)
            return

        if tile == TileType.STAIRS_DOWN.value:
            if self.game_map.current_level >= MAX_LEVELS:
                if self.boss_defeated:
                    self.trigger_victory()
                else:
                    self.add_message("A powerful presence blocks your path.")
            else:
                self.add_message("You descend deeper...")
                self.next_level()

    def grant_quest_rewards(self) -> None:
        for quest in self.quest_log.get_quests():
            if not getattr(quest, "completed", False):
                continue
            if quest.title in self.rewarded_quests:
                continue

            reward = quest.reward
            if isinstance(reward, dict):
                if "gold" in reward:
                    self.player.gold += reward["gold"]
                    self.add_message(f"Quest '{quest.title}' reward: +{reward['gold']} gold")
                if "exp" in reward:
                    self.player.experience += reward["exp"]
                    self.add_message(f"Quest '{quest.title}' reward: +{reward['exp']} EXP")
                if "item" in reward and reward["item"] in self.items:
                    self.player.add_item(self.items[reward["item"]])
                    self.add_message(f"Quest '{quest.title}' reward: {self.items[reward['item']].name}")

            self.rewarded_quests.add(quest.title)

    def combat(self, actor: Player, monster: Monster) -> None:
        _safe_play(self.sword_sound)
        while monster.health > 0 and actor.is_alive():
            damage = max(1, actor.attack - monster.defense)
            monster.health -= damage
            self.add_message(f"You deal {damage} to {monster.name}.")

            if monster.health <= 0:
                exp_gain = getattr(monster, "exp", 20)
                gold_gain = getattr(monster, "gold", random.randint(10, 30))
                actor.experience += exp_gain
                actor.gold += gold_gain
                self.add_message(f"You defeated {monster.name}!")
                self.add_message(f"Rewards: +{exp_gain} EXP, +{gold_gain} gold")

                if self.quest_log.complete_quest(monster.name.lower()):
                    self.grant_quest_rewards()

                if monster.name.lower() == "dragon":
                    self.boss_defeated = True
                break

            mdmg = max(1, monster.attack - actor.defense)
            actor.take_damage(mdmg)
            self.add_message(f"{monster.name} hits you for {mdmg}.")

            if not actor.is_alive():
                self.add_message(f"{'P1' if actor is self.player else 'P2'} has fallen.")

        if not self.player.is_alive() and (not self.multiplayer or not self.player2.is_alive()):
            self.add_message("Both adventurers have fallen.")
            self.state = GameState.GAME_OVER
        elif actor.is_alive():
            self.add_message(f"{'P1' if actor is self.player else 'P2'} health: {actor.health}")

        self.check_level_up(actor)
        self.grant_quest_rewards()

    def use_inventory_item(self, item_index: int, mouse_button: int) -> None:
        items = self.player.inventory  # shared inventory
        if item_index < 0 or item_index >= len(items):
            return

        target = self.get_inventory_target()
        if not target.is_alive():
            self.add_message(
                f"Cannot use items on {self.inventory_target_names[self.active_player]} because they are dead."
            )
            return

        item = items[item_index]
        if mouse_button == 1:
            self.add_message(item.use(target))
        elif mouse_button == 3:
            self.add_message(item.sell(target))

    def undo_move(self) -> None:
        if self.move_stack.is_empty():
            self.add_message("No moves to undo.")
            return
        last_pos = self.move_stack.pop()
        if last_pos is None:
            return
        self.player.x, self.player.y = last_pos
        self.add_message(f"Undo -> ({self.player.x}, {self.player.y})")
        self.game_map.reveal_area(self.player.x, self.player.y)

    def next_level(self) -> None:
        self.game_map.current_level += 1
        if self.game_map.current_level > MAX_LEVELS:
            self.trigger_victory()
            return

        self.game_map.generate_map()
        self.ensure_valid_map(initial=False)
        self.add_message(f"Welcome to level {self.game_map.current_level}.")

        if self.game_map.current_level >= MAX_LEVELS:
            self.add_message("A terrifying presence fills the air...")

    def trigger_victory(self) -> None:
        total_time = time.time() - (self.start_time or time.time())
        self.add_message(f"Dungeon completed in {total_time:.1f}s.")
        if self.highscore is None or total_time < self.highscore:
            self.highscore = total_time
            self.save_highscore(total_time)
            self.add_message("New highscore!")
        self.state = GameState.VICTORY

