#Author Viom Shrestha
import random
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

BASE_MONSTERS = {
    "lizard": {"health": 30, "attack": 8,  "defense": 3,  "sprite": "lizard.png", "exp": 15,  "gold": 10},
    "snake":  {"health": 40, "attack": 12, "defense": 6,  "sprite": "snake.png",  "exp": 16,  "gold": 11},
    "jinn":   {"health": 50, "attack": 15, "defense": 8,  "sprite": "jinn.png",   "exp": 40,  "gold": 30},
    "demon":  {"health": 60, "attack": 18, "defense": 10, "sprite": "demon.png",  "exp": 50,  "gold": 40},
    "dragon": {"health": 110,"attack": 20, "defense": 16, "sprite": "dragon.png", "exp": 200, "gold": 200},
}

MAP_SIZES = {
    "easy":   (15, 10),
    "normal": (20, 15),
    "hard":   (25, 20),
}


class TileType(Enum):
    EMPTY       = " "
    WALL        = "#"
    TREASURE    = "T"
    MONSTER     = "M"
    STAIRS_UP   = "U"
    STAIRS_DOWN = "d"
    PLAYER      = "P"


class Item:
    def __init__(self, name: str, description: str, value: int, item_type: str, effect_value: int = 0):
        self.name = name
        self.description = description
        self.value = value
        self.item_type = item_type  # "weapon", "armor", "consumable"
        self.effect_value = effect_value

    def use(self, target: "Player") -> str:
        if self.item_type == "weapon":
            if target.equipped_weapon:
                target.attack -= target.equipped_weapon.effect_value
                target.inventory.append(target.equipped_weapon)
            target.equipped_weapon = self
            target.attack += self.effect_value
            target.inventory.remove(self)
            return f"{target.name} equipped {self.name} (+{self.effect_value} ATK)"

        elif self.item_type == "armor":
            if target.equipped_armor:
                target.defense -= target.equipped_armor.effect_value
                target.inventory.append(target.equipped_armor)
            target.equipped_armor = self
            target.defense += self.effect_value
            target.inventory.remove(self)
            return f"{target.name} equipped {self.name} (+{self.effect_value} DEF)"

        elif self.item_type == "consumable":
            heal = int(getattr(self, "effect_value", 0))
            target.health = min(target.max_health, target.health + heal)
            target.inventory.remove(self)
            return f"{target.name} healed +{heal} HP"

        return f"{self.name} cannot be used."

    def sell(self, target: "Player") -> str:
        value = int(getattr(self, "value", 10))
        target.gold += value
        target.inventory.remove(self)
        return f"{target.name} sold {self.name} for {value} gold"


class Monster:
    def __init__(self, name: str, health: int, attack: int, defense: int, sprite: Optional[str] = None):
        self.name = name
        self.health = health
        self.attack = attack
        self.defense = defense
        self.max_health = health
        self.sprite = sprite


class Quest:
    def __init__(self, title: str, description: str, target: str, reward: Dict[str, Any]):
        self.title = title
        self.description = description
        self.target = target
        self.reward = reward
        self.completed = False


# Linked List Node for Quest
class QuestNode:
    def __init__(self, quest: Quest):
        self.quest = quest
        self.next = None


# Linked List for Quest Log
class QuestLog:
    def __init__(self):
        self.head = None
        self.size = 0

    def add_quest(self, quest: Quest):
        new_node = QuestNode(quest)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self.size += 1

    def get_quests(self) -> List[Quest]:
        quests = []
        current = self.head
        while current:
            quests.append(current.quest)
            current = current.next
        return quests

    def complete_quest(self, target: str):
        current = self.head
        while current:
            if current.quest.target == target and not current.quest.completed:
                current.quest.completed = True
                return True
            current = current.next
        return False


# Stack for Undo/Backtrack
class MoveStack:
    def __init__(self):
        self.moves = []

    def push(self, move: Tuple[int, int]):
        self.moves.append(move)

    def pop(self) -> Optional[Tuple[int, int]]:
        if self.moves:
            return self.moves.pop()
        return None

    def peek(self) -> Optional[Tuple[int, int]]:
        if self.moves:
            return self.moves[-1]
        return None

    def is_empty(self) -> bool:
        return len(self.moves) == 0


# Queue for Turn-based Actions
class ActionQueue:
    def __init__(self):
        self.actions = []

    def enqueue(self, action: str):
        self.actions.append(action)

    def dequeue(self) -> Optional[str]:
        if self.actions:
            return self.actions.pop(0)
        return None

    def is_empty(self) -> bool:
        return len(self.actions) == 0

    def size(self) -> int:
        return len(self.actions)


class Player:
    def __init__(self, x: int, y: int, name: str = "Hero"):
        self.x = x
        self.y = y
        self.name = name
        self.health = 100
        self.max_health = 100
        self.base_attack = 15
        self.base_defense = 10
        self.attack = self.base_attack
        self.defense = self.base_defense
        self.level = 1
        self.experience = 0
        self.inventory: List[Item] = []
        self.equipped_weapon: Optional[Item] = None
        self.equipped_armor: Optional[Item] = None
        self.gold = 0

    def add_item(self, item: Item):
        self.inventory.append(item)

    def remove_item(self, item_name: str) -> Optional[Item]:
        for i, item in enumerate(self.inventory):
            if item.name.lower() == item_name.lower():
                return self.inventory.pop(i)
        return None

    def heal(self, amount: int):
        self.health = min(self.max_health, self.health + amount)

    def take_damage(self, amount: int):
        self.health = max(0, self.health - amount)

    def is_alive(self) -> bool:
        return self.health > 0


class GameMap:
    def __init__(self, width: int, height: int, difficulty: str = "normal"):
        self.width = width
        self.height = height
        self.difficulty = difficulty
        self.map_data: List[List[str]] = []
        self.visible_map: List[List[bool]] = []
        self.player_start = (1, 1)
        self.current_level = 1
        self.generate_map()

    def generate_map(self):
        self.map_data = [[TileType.EMPTY.value for _ in range(self.width)] for _ in range(self.height)]
        self.visible_map = [[False for _ in range(self.width)] for _ in range(self.height)]

        for x in range(self.width):
            self.map_data[0][x] = TileType.WALL.value
            self.map_data[self.height - 1][x] = TileType.WALL.value
        for y in range(self.height):
            self.map_data[y][0] = TileType.WALL.value
            self.map_data[y][self.width - 1] = TileType.WALL.value

        self.map_data[self.player_start[1]][self.player_start[0]] = TileType.EMPTY.value

        if self.difficulty == "easy":
            wall_count, treasure_count, monster_count = self.width * self.height // 12, 4, 3
        elif self.difficulty == "hard":
            wall_count, treasure_count, monster_count = self.width * self.height // 8, 10, 7
        else:
            wall_count, treasure_count, monster_count = self.width * self.height // 10, 7, 5

        for _ in range(wall_count):
            x, y = random.randint(1, self.width - 2), random.randint(1, self.height - 2)
            self.map_data[y][x] = TileType.WALL.value

        for _ in range(treasure_count):
            x, y = random.randint(1, self.width - 2), random.randint(1, self.height - 2)
            if self.map_data[y][x] == TileType.EMPTY.value:
                self.map_data[y][x] = TileType.TREASURE.value

        for _ in range(monster_count):
            x, y = random.randint(1, self.width - 2), random.randint(1, self.height - 2)
            if self.map_data[y][x] == TileType.EMPTY.value:
                self.map_data[y][x] = TileType.MONSTER.value

        x, y = random.randint(1, self.width - 2), random.randint(1, self.height - 2)
        if self.map_data[y][x] == TileType.EMPTY.value:
            self.map_data[y][x] = TileType.STAIRS_DOWN.value

        if self.current_level == 5:
            tries, placed = 0, False
            while tries < 500 and not placed:
                x, y = random.randint(1, self.width - 2), random.randint(1, self.height - 2)
                if self.map_data[y][x] == TileType.EMPTY.value:
                    self.map_data[y][x] = f"{TileType.MONSTER.value}:dragon"
                    placed = True
                tries += 1

    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int) -> str:
        if self.is_valid_position(x, y):
            return self.map_data[y][x]
        return TileType.WALL.value

    def set_tile(self, x: int, y: int, tile_type: str):
        if self.is_valid_position(x, y):
            self.map_data[y][x] = tile_type

    def reveal_area(self, center_x: int, center_y: int, radius: int = 3):
        def reveal_recursive(x: int, y: int, remaining_radius: int):
            if not self.is_valid_position(x, y) or remaining_radius < 0:
                return
            self.visible_map[y][x] = True
            if remaining_radius > 0:
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    reveal_recursive(x + dx, y + dy, remaining_radius - 1)

        reveal_recursive(center_x, center_y, radius)


class DungeonCrawler:
    """Factory / helper class used by the GUI to create monsters, items, and quests."""

    def __init__(self, difficulty: str = "normal"):
        self.difficulty = difficulty

    def get_map_size_by_difficulty(self) -> Tuple[int, int]:
        return MAP_SIZES.get(self.difficulty, MAP_SIZES["normal"])

    def create_monsters(self) -> Dict[str, Monster]:
        scale_factor = {"easy": 0.7, "hard": 1.5}.get(self.difficulty, 1.0)
        monsters = {}
        for name, stats in BASE_MONSTERS.items():
            m = Monster(
                name,
                int(stats["health"] * scale_factor),
                int(stats["attack"] * scale_factor),
                int(stats["defense"] * scale_factor),
                stats.get("sprite"),
            )
            setattr(m, "exp",  stats.get("exp",  20))
            setattr(m, "gold", stats.get("gold", 10))
            monsters[name] = m
        return monsters

    def create_items(self) -> Dict[str, Item]:
        return {
            "sword":         Item("Iron Sword",              "A sharp iron sword",              50,  "weapon",     5),
            "steel_sword":   Item("Steel Sword",             "A superior steel sword",           80,  "weapon",     8),
            "magic_sword":   Item("Magic Sword",             "A sword with magical properties", 150,  "weapon",    12),
            "shield":        Item("Wooden Shield",           "A sturdy wooden shield",           30,  "armor",      3),
            "iron_shield":   Item("Iron Shield",             "A strong iron shield",             60,  "armor",      6),
            "magic_shield":  Item("Magic Shield",            "A shield with magical protection",120,  "armor",     10),
            "potion":        Item("Health Potion",           "Restores 25 health",               25,  "consumable", 25),
            "greater_potion":Item("Greater Health Potion",  "Restores 50 health",               50,  "consumable", 50),
            "super_potion":  Item("Super Health Potion",    "Restores 100 health",             100,  "consumable",100),
        }

    @staticmethod
    def get_default_quests():
        return [
            Quest("Jinn Hunter",        "Defeat 1 jinn",                 "jinn",    {"gold": 50,  "exp": 50}),
            Quest("Treasure Collector", "Collect 1 treasure",            "treasure",{"item": "steel_sword"}),
            Quest("Demon Slayer",       "Defeat the demon on depth 10",  "demon",   {"item": "magic_shield", "gold": 200, "exp": 200}),
        ]
