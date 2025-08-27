#Author Viom Shrestha
import random
import time
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

BASE_MONSTERS = {
    "lizard": {"health": 30, "attack": 8, "defense": 3, "sprite": "lizard.png", "exp": 15, "gold": 10},
    "snake": {"health": 40, "attack": 12, "defense": 6, "sprite": "snake.png", "exp": 16, "gold": 11},
    "jinn": {"health": 50, "attack": 15, "defense": 8, "sprite": "jinn.png", "exp": 40, "gold": 30},
    "demon": {"health": 60, "attack": 18, "defense": 10, "sprite": "demon.png", "exp": 50, "gold": 40},
    "dragon": {"health": 110, "attack": 20, "defense": 16, "sprite": "dragon.png", "exp": 200, "gold": 200},
}
    
MAP_SIZES = {
    "easy": (15, 10),
    "normal": (20, 15),
    "hard": (25, 20),
}


class TileType(Enum):
    EMPTY = " "
    WALL = "#"
    TREASURE = "T"
    MONSTER = "M"
    STAIRS_UP = "U"
    STAIRS_DOWN = "d"
    PLAYER = "P"

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
        self.sprite = sprite  # New attribute for the sprite name

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

# Stack for Undo/Backtrack feature
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
        self.inventory: List[Item] = []  # 1D List for inventory
        self.equipped_weapon: Optional[Item] = None
        self.equipped_armor: Optional[Item] = None
        self.gold = 0
    
    def add_item(self, item: Item):
        self.inventory.append(item)
        print(f"Added {item.name} to inventory!")
    
    def remove_item(self, item_name: str) -> Optional[Item]:
        for i, item in enumerate(self.inventory):
            if item.name.lower() == item_name.lower():
                return self.inventory.pop(i)
        return None
    
    def use_item(self, item_name: str) -> bool:
        """Use an item from inventory"""
        item = self.remove_item(item_name)
        if not item:
            print(f"You don't have {item_name} in your inventory.")
            return False
        
        if item.item_type == "consumable":
            if "potion" in item.name.lower():
                self.heal(item.effect_value)
                print(f"You used {item.name} and restored {item.effect_value} health!")
                return True
            else:
                print(f"You can't use {item.name}.")
                self.add_item(item)  # Put it back
                return False
        
        elif item.item_type == "weapon":
            if self.equipped_weapon:
                self.unequip_weapon()
            self.equip_weapon(item)
            return True
        
        elif item.item_type == "armor":
            if self.equipped_armor:
                self.unequip_armor()
            self.equip_armor(item)
            return True
        
        else:
            print(f"You can't use {item.name}.")
            self.add_item(item)  # Put it back
            return False
    
    def equip_weapon(self, weapon: Item):
        """Equip a weapon"""
        self.equipped_weapon = weapon
        self.attack = self.base_attack + weapon.effect_value
        print(f"Equipped {weapon.name}! Attack increased to {self.attack}")
    
    def unequip_weapon(self):
        """Unequip current weapon"""
        if self.equipped_weapon:
            print(f"Unequipped {self.equipped_weapon.name}")
            self.attack = self.base_attack
            self.inventory.append(self.equipped_weapon)
            self.equipped_weapon = None
    
    def equip_armor(self, armor: Item):
        """Equip armor"""
        self.equipped_armor = armor
        self.defense = self.base_defense + armor.effect_value
        print(f"Equipped {armor.name}! Defense increased to {self.defense}")
    
    def unequip_armor(self):
        """Unequip current armor"""
        if self.equipped_armor:
            print(f"Unequipped {self.equipped_armor.name}")
            self.defense = self.base_defense
            self.inventory.append(self.equipped_armor)
            self.equipped_armor = None
    
    def show_inventory(self):
        if not self.inventory:
            print("Inventory is empty.")
            return
        
        print("\n=== INVENTORY ===")
        for i, item in enumerate(self.inventory, 1):
            item_type_info = f"({item.item_type.title()})"
            if item.item_type == "weapon":
                item_type_info += f" +{item.effect_value} ATK"
            elif item.item_type == "armor":
                item_type_info += f" +{item.effect_value} DEF"
            elif item.item_type == "consumable":
                item_type_info += f" +{item.effect_value} HP"
            
            print(f"{i}. {item.name} - {item.description} {item_type_info} (Value: {item.value})")
        
        print("\n=== EQUIPPED ===")
        if self.equipped_weapon:
            print(f"Weapon: {self.equipped_weapon.name} (+{self.equipped_weapon.effect_value} ATK)")
        else:
            print("Weapon: None")
        
        if self.equipped_armor:
            print(f"Armor: {self.equipped_armor.name} (+{self.equipped_armor.effect_value} DEF)")
        else:
            print("Armor: None")
    
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
        self.map_data: List[List[str]] = []  # 2D Matrix for game map
        self.visible_map: List[List[bool]] = []  # Fog of war
        self.player_start = (1, 1)
        self.current_level = 1
        self.generate_map()
    
    def generate_map(self):
        # Initialize empty map
        self.map_data = [[TileType.EMPTY.value for _ in range(self.width)] for _ in range(self.height)]
        self.visible_map = [[False for _ in range(self.width)] for _ in range(self.height)]
        
        
        # Add walls around the border
        for x in range(self.width):
            self.map_data[0][x] = TileType.WALL.value
            self.map_data[self.height-1][x] = TileType.WALL.value
        
        for y in range(self.height):
            self.map_data[y][0] = TileType.WALL.value
            self.map_data[y][self.width-1] = TileType.WALL.value
        
        # Ensure player start is clear
        self.map_data[self.player_start[1]][self.player_start[0]] = TileType.EMPTY.value
        
        # Difficulty-based map generation
        if self.difficulty == "easy":
            wall_count = self.width * self.height // 12
            treasure_count = 3
            monster_count = 2
        elif self.difficulty == "hard":
            wall_count = self.width * self.height // 8
            treasure_count = 7
            monster_count = 5
        else:  # normal
            wall_count = self.width * self.height // 10
            treasure_count = 5
            monster_count = 3
        
        # Add random walls
        for _ in range(wall_count):
            x = random.randint(1, self.width-2)
            y = random.randint(1, self.height-2)
            self.map_data[y][x] = TileType.WALL.value
        
        # Add treasures
        for _ in range(treasure_count):
            x = random.randint(1, self.width-2)
            y = random.randint(1, self.height-2)
            if self.map_data[y][x] == TileType.EMPTY.value:
                self.map_data[y][x] = TileType.TREASURE.value
        
        # Add monsters
        for _ in range(monster_count):
            x = random.randint(1, self.width-2)
            y = random.randint(1, self.height-2)
            if self.map_data[y][x] == TileType.EMPTY.value:
                self.map_data[y][x] = TileType.MONSTER.value  # just plain "M"
        # Add stairs
        x = random.randint(1, self.width-2)
        y = random.randint(1, self.height-2)
        if self.map_data[y][x] == TileType.EMPTY.value:
            self.map_data[y][x] = TileType.STAIRS_DOWN.value
        # If this is level 10, ensure there's exactly one dragon tile somewhere
        if self.current_level == 10:
            tries = 0
            placed = False
            while tries < 500 and not placed:
                x = random.randint(1, self.width - 2)
                y = random.randint(1, self.height - 2)
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
        """Recursive function to reveal fog of war around player"""
        def reveal_recursive(x: int, y: int, remaining_radius: int):
            if not self.is_valid_position(x, y) or remaining_radius < 0:
                return
            
            self.visible_map[y][x] = True
            
            if remaining_radius > 0:
                # Reveal adjacent tiles recursively
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    reveal_recursive(x + dx, y + dy, remaining_radius - 1)
        
        reveal_recursive(center_x, center_y, radius)
    
    def display_map(self, player_x: int, player_y: int):
        """Display the map with fog of war and player position"""
        print(f"\n=== LEVEL {self.current_level} ===")
        print("Legend: #=Wall, T=Treasure, M=Monster, d=Stairs, P=Player")
        print("=" * (self.width + 2))
        
        for y in range(self.height):
            row = "|"
            for x in range(self.width):
                if x == player_x and y == player_y:
                    row += "P"
                elif self.visible_map[y][x]:
                    row += self.map_data[y][x]
                else:
                    row += "?"  # Fog of war
            row += "|"
            print(row)
        
        print("=" * (self.width + 2))

class DungeonCrawler:
    def __init__(self, difficulty: str = "normal"):
        self.difficulty = difficulty
        self.map_size = self.get_map_size_by_difficulty()
        self.player = Player(1, 1)
        self.quest_log = QuestLog()
        self.move_stack = MoveStack()
        self.action_queue = ActionQueue()
        self.game_running = True
        self.monsters = self.create_monsters()
        self.items = self.create_items()
        self.rewarded_quests = set()  # track rewards given
        self.initialize_quests()
        self.game_map = GameMap(self.map_size[0], self.map_size[1], difficulty)
        
        # Reveal starting area
        self.game_map.reveal_area(self.player.x, self.player.y)
    
    def get_map_size_by_difficulty(self) -> Tuple[int, int]:
        return MAP_SIZES.get(self.difficulty, MAP_SIZES["normal"])
    
    def create_monsters(self) -> Dict[str, Monster]:
        scale_factor = 1.0
        if self.difficulty == "easy":
            scale_factor = 0.7
        elif self.difficulty == "hard":
            scale_factor = 1.5

        monsters = {}
        for name, stats in BASE_MONSTERS.items():
            m = Monster(
                name,
                int(stats["health"] * scale_factor),
                int(stats["attack"] * scale_factor),
                int(stats["defense"] * scale_factor),
                stats.get("sprite")
            )
            # attach per-species rewards
            setattr(m, "exp", stats.get("exp", 20))
            setattr(m, "gold", stats.get("gold", 10))
            monsters[name] = m
        return monsters
    
    def create_items(self) -> Dict[str, Item]:
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
        }

    @staticmethod
    def get_default_quests():
        return [
            Quest("Jinn Hunter", "Defeat 1 jinn", "jinn", {"gold": 50, "exp": 50}),
            Quest("Treasure Collector", "Collect 1 treasure", "treasure", {"item": "steel_sword"}),
            Quest("Demon Slayer", "Defeat the demon on depth 10", "demon",
                {"item": "magic_shield", "gold": 200, "exp": 200}),
        ]
    def initialize_quests(self):
        for quest in DungeonCrawler.get_default_quests():
            self.quest_log.add_quest(quest)
    
    def process_command(self, command: str):
        """Main command processing function with loops"""
        command = command.lower().strip()
        
        if command in ["north", "w"]:
            self.move_player(0, -1)
        elif command in ["south", "s"]:
            self.move_player(0, 1)
        elif command in ["east", "d"]:
            self.move_player(1, 0)
        elif command in ["west", "a"]:
            self.move_player(-1, 0)
        elif command.startswith("use "):
            item_name = command[4:]
            self.player.use_item(item_name)
        elif command.startswith("get "):
            item_name = command[4:]
            self.get_item(item_name)
        elif command == "inventory" or command == "i":
            self.player.show_inventory()
        elif command == "status" or command == "s":
            self.show_status()
        elif command == "quests" or command == "q":
            self.show_quests()
        elif command == "undo" or command == "u":
            self.undo_move()
        elif command == "help" or command == "h":
            self.show_help()
        elif command == "quit" or command == "exit":
            self.game_running = False
        else:
            print(f"Unknown command: {command}")
    
    def move_player(self, dx: int, dy: int):
        """Move player and handle tile interactions"""
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        if not self.game_map.is_valid_position(new_x, new_y):
            print("You can't move there!")
            return
        
        tile = self.game_map.get_tile(new_x, new_y)
        
        if tile == TileType.WALL.value:
            print("You can't walk through walls!")
            return
        
        # Save current position to move stack for undo
        self.move_stack.push((self.player.x, self.player.y))
        
        # Update player position
        self.player.x = new_x
        self.player.y = new_y
        
        # Handle tile interactions
        self.handle_tile_interaction(tile, new_x, new_y)
        
        # Reveal new area
        self.game_map.reveal_area(self.player.x, self.player.y)
        
        # Process monster turns
        self.process_monster_turns()
    
    def handle_tile_interaction(self, tile: str, x: int, y: int):

        if tile == TileType.TREASURE.value:
            print("You found a treasure!")
            # Random item from treasure
            item_name = random.choice(list(self.items.keys()))
            item = self.items[item_name]
            self.player.add_item(item)
            self.game_map.set_tile(x, y, TileType.EMPTY.value)
            
            quest = self.quest_log.complete_quest("treasure")
            if quest:
                self.grant_quest_rewards()
        elif tile.startswith(TileType.MONSTER.value):
            parts = tile.split(":")
            if len(parts) > 1:
                monster_name = parts[1]          # explicit monster on the tile
            else:
                pool = list(self.monsters.keys())
                # exclude dragon unless we're on level 10
                if self.game_map.current_level < 10 and "dragon" in pool:
                    pool.remove("dragon")
                monster_name = random.choice(pool)

            monster = self.monsters[monster_name]
            print(f"A {monster.name} appears!")
            self.combat(monster)
            self.check_level_up()
            self.game_map.set_tile(x, y, TileType.EMPTY.value)

        elif tile == TileType.STAIRS_DOWN.value:
            print("You found stairs leading deeper into the dungeon!")
            self.next_level()
        
    def check_level_up(self):
        exp_needed = 50 + (self.player.level * 10)
        if self.player.experience >= exp_needed:
            self.player.level += 1
            self.player.experience -= exp_needed
            self.player.max_health += 10
            self.player.base_attack += 2
            self.player.base_defense += 2
            print(f"LEVEL UP! You are now level {self.player.level}!")

    def combat(self, monster: Monster):
        print(f"\n=== COMBAT: {monster.name} ===")
        # Clone a fresh mob for this encounter
        mob = Monster(monster.name, monster.health, monster.attack, monster.defense, monster.sprite)
        setattr(mob, "exp", getattr(monster, "exp", 20))
        setattr(mob, "gold", getattr(monster, "gold", 10))

        while mob.health > 0 and self.player.is_alive():
            dmg = max(1, self.player.attack - mob.defense)
            mob.health -= dmg
            print(f"You deal {dmg} damage to {mob.name}!")

            if mob.health <= 0:
                print(f"You defeated {mob.name}!")
                exp_gain = getattr(mob, "exp", 20)
                gold_gain = getattr(mob, "gold", random.randint(10, 30))
                self.player.experience += exp_gain
                self.player.gold += gold_gain
                print(f"Rewards: +{exp_gain} EXP, +{gold_gain} Gold")

                # Quest check (use the exact monster key)
                if self.quest_log.complete_quest(mob.name.lower()):
                    self.grant_quest_rewards()
                if mob.name.lower() == "dragon":
                    print("You have slain the Dragon!")
                break

            # Monster turn
            mdmg = max(1, mob.attack - self.player.defense)
            self.player.take_damage(mdmg)
            print(f"{mob.name} deals {mdmg} damage to you!")

            if not self.player.is_alive():
                print("You have been defeated!")
                break

        if self.player.is_alive():
            print(f"Combat ended. Your health: {self.player.health}")


    def grant_quest_rewards(self):
        for q in self.quest_log.get_quests():
            if q.completed and q.title not in self.rewarded_quests:
                reward = q.reward or {}
                if "gold" in reward:
                    amt = int(reward["gold"])
                    self.player.gold += amt
                    print(f"Quest '{q.title}' reward: +{amt} Gold")
                if "exp" in reward:
                    xp = int(reward["exp"])
                    self.player.experience += xp
                    print(f"Quest '{q.title}' reward: +{xp} EXP")
                if "item" in reward and reward["item"] in self.items:
                    item = self.items[reward["item"]]
                    self.player.add_item(item)
                    print(f"Quest '{q.title}' reward: {item.name}")
                self.rewarded_quests.add(q.title)
                print(f"Quest Completed: {q.title}")


    def process_monster_turns(self):
        """Process monster actions using queue"""
        # Add monster actions to queue
        for monster_name, monster in self.monsters.items():
            if monster.health > 0:
                self.action_queue.enqueue(f"{monster_name} patrols")
                self.action_queue.enqueue(f"{monster_name} searches for prey")
        
        # Process some actions
        actions_processed = 0
        while not self.action_queue.is_empty() and actions_processed < 2:
            action = self.action_queue.dequeue()
            if action:
                print(f"Monster action: {action}")
                actions_processed += 1
    
    def undo_move(self):
        """Undo last move using stack"""
        if self.move_stack.is_empty():
            print("No moves to undo!")
            return
        
        last_pos = self.move_stack.pop()
        self.player.x, self.player.y = last_pos
        print(f"Undid move. Back at position ({self.player.x}, {self.player.y})")
        self.game_map.reveal_area(self.player.x, self.player.y)
    
    def next_level(self):
        """Generate next level"""
        self.game_map.current_level += 1
        self.game_map.generate_map()
        self.player.x, self.player.y = self.game_map.player_start
        self.game_map.reveal_area(self.player.x, self.player.y)
        print(f"Welcome to level {self.game_map.current_level}!")
    
    def show_status(self):
        """Show player status"""
        print(f"\n=== PLAYER STATUS ===")
        print(f"Health: {self.player.health}/{self.player.max_health}")
        print(f"Level: {self.player.level}")
        print(f"Experience: {self.player.experience}")
        print(f"Gold: {self.player.gold}")
        print(f"Attack: {self.player.attack} (Base: {self.player.base_attack})")
        print(f"Defense: {self.player.defense} (Base: {self.player.base_defense})")
        print(f"Position: ({self.player.x}, {self.player.y})")
        print(f"Difficulty: {self.difficulty.title()}")
    
    def show_quests(self):
        """Show current quests"""
        quests = self.quest_log.get_quests()
        if not quests:
            print("No quests available.")
            return
        
        print("\n=== ACTIVE QUESTS ===")
        for i, quest in enumerate(quests, 1):
            status = "✓" if quest.completed else "○"
            print(f"{i}. [{status}] {quest.title}")
            print(f"   {quest.description}")
            print(f"   Reward: {quest.reward}")
    
    def show_help(self):
        """Show available commands"""
        print("\n=== AVAILABLE COMMANDS ===")
        print("Movement: north/w, south/s, east/d, west/a")
        print("Actions: use <item>, inventory/i, status/s")
        print("Game: quests/q, undo/u, help/h, quit/exit")
        print("\n=== ITEM USAGE ===")
        print("• Use 'use <item>' to equip weapons/armor or consume potions")
        print("• Weapons increase attack, armor increases defense")
        print("• Potions restore health")
    
    def run(self):
        """Main game loop"""
        print("Welcome to Dungeon Crawler!")
        print(f"Difficulty: {self.difficulty.title()}")
        print(f"Map Size: {self.map_size[0]}x{self.map_size[1]}")
        print("Type 'help' for available commands.")
        print("Good luck!\n")
        print(f"{self.show_help()} \n")

        while self.game_running:
            self.game_map.display_map(self.player.x, self.player.y)
            self.show_status()
            
            command = input("\nWhat would you like to do? ").strip()
            if command:
                self.process_command(command)
            
            # Check if player is dead
            if not self.player.is_alive():
                print("\nGame Over! You have been defeated.")
                self.game_running = False
                break
            
            time.sleep(0.5)  # Small delay for better readability
        
        print("Thanks for playing Dungeon Crawler!")

def select_difficulty() -> str:
    """Let player select game difficulty"""
    print("=== DUNGEON CRAWLER - DIFFICULTY SELECTION ===")
    print("1. Easy - Smaller map, fewer monsters, weaker enemies")
    print("2. Normal - Balanced gameplay")
    print("3. Hard - Larger map, more monsters, stronger enemies")
    
    while True:
        choice = input("\nSelect difficulty (1-3): ").strip()
        if choice == "1":
            return "easy"
        elif choice == "2":
            return "normal"
        elif choice == "3":
            return "hard"
        else:
            print("Please enter 1, 2, or 3.")

def main():
    """Main function to start the game"""
    difficulty = select_difficulty()
    game = DungeonCrawler(difficulty)
    game.run()

if __name__ == "__main__":
    main()
