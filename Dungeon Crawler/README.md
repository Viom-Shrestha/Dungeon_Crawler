# Dungeon Crawler - Text-Based Adventure Game

A classic text-based adventure game where players navigate through a procedurally generated dungeon, battle monsters, collect treasures, and complete quests.

## 🎮 Game Features

### Core Gameplay
- **2D Matrix Map**: The game world is represented as a 2D matrix with different tile types
- **Fog of War**: Only areas near the player are visible, creating exploration mechanics
- **Procedural Generation**: Each level is randomly generated with walls, doors, treasures, and monsters
- **Turn-based Combat**: Strategic combat system with attack and defense mechanics
- **Difficulty Settings**: Three difficulty levels affecting map size, monster strength, and item distribution

### Data Structures Implementation

#### 📋 Lists & Matrices
- **2D Matrix**: Game map stored as `List[List[str]]` for efficient tile access
- **1D List**: Player inventory managed as a simple list of items

#### 🔄 Recursion
- **Fog of War**: Recursive algorithm reveals map tiles around the player
- **Pathfinding**: Recursive exploration of adjacent tiles with radius-based visibility

#### ⚙️ Functions & Loops
- **Main Game Loop**: Continuous loop processing player commands and game state
- **Command Processing**: Function-based command handling with input validation
- **Map Generation**: Loops for creating walls, doors, treasures, and monsters

#### 🔗 Linked Lists
- **Quest System**: Quest log implemented as a linked list for dynamic quest management
- **Quest Nodes**: Each quest stored as a node with completion status tracking

#### 📚 Stacks & Queues
- **Move Stack**: Undo/backtrack feature using a stack to store previous positions
- **Action Queue**: Turn-based monster actions managed with a queue system

## 🎯 How to Play

### Starting the Game
```bash
python dungeon_crawler.py
```

### Difficulty Selection
The game starts with difficulty selection:
1. **Easy**: 15x10 map, fewer monsters, weaker enemies
2. **Normal**: 20x15 map, balanced gameplay
3. **Hard**: 25x20 map, more monsters, stronger enemies

### Available Commands
- **Movement**: `north`/`w`, `south`/`s`, `east`/`d`, `west`/`a`
- **Actions**: `use <item>`, `get <item>`, `inventory`/`i`, `status`/`s`
- **Game**: `quests`/`q`, `undo`/`u`, `help`/`h`, `quit`/`q`

### Game Elements
- **#**: Wall (impassable)
- **D**: Door (requires key to unlock)
- **T**: Treasure (collectible items)
- **M**: Monster (initiates combat)
- **d**: Stairs (advance to next level)
- **P**: Player position
- **?**: Unexplored area (fog of war)

## 🛡️ Equipment & Item System

### Item Types
- **Weapons**: Increase attack power when equipped
- **Armor**: Increase defense when equipped
- **Consumables**: Potions that restore health
- **Keys**: Automatically used to unlock doors
- **Treasure**: Valuable items for collection

### Using Items
- **`use <item>`**: Equip weapons/armor or consume potions
- **Automatic Equipping**: Weapons and armor are automatically equipped when used
- **Unequipping**: Previous equipment is automatically unequipped and returned to inventory

### Item Examples
- **Iron Sword**: +5 Attack
- **Steel Sword**: +8 Attack
- **Magic Sword**: +12 Attack
- **Wooden Shield**: +3 Defense
- **Iron Shield**: +6 Defense
- **Magic Shield**: +10 Defense
- **Health Potion**: +25 HP
- **Greater Potion**: +50 HP
- **Super Potion**: +100 HP

## 🏗️ Architecture

### Class Structure
1. **`DungeonCrawler`**: Main game controller with difficulty management
2. **`Player`**: Player character with stats, inventory, and equipment system
3. **`GameMap`**: 2D matrix representing the game world with difficulty scaling
4. **`QuestLog`**: Linked list for quest management
5. **`MoveStack`**: Stack for undo functionality
6. **`ActionQueue`**: Queue for monster turn management
7. **`Item`**: Enhanced game items with types and effects
8. **`Monster`**: Enemy creatures with difficulty-based scaling
9. **`Quest`**: Quest objectives and rewards

### Key Algorithms
- **Map Generation**: Random placement of game elements with difficulty-based counts
- **Fog of War**: Recursive tile revelation
- **Combat System**: Turn-based damage calculation with equipment bonuses
- **Quest Tracking**: Linked list traversal for completion checks
- **Difficulty Scaling**: Monster stats and map generation based on selected difficulty

## 🚀 Running the Game

### Prerequisites
- Python 3.7+ (for type hints support)
- No external packages required

### Quick Start
1. Navigate to the Dungeon Crawler directory
2. Run `python dungeon_crawler.py`
3. Select difficulty level (1-3)
4. Type `help` to see available commands
5. Start exploring with movement commands!

## 🎲 Game Mechanics

### Combat
- Turn-based system with attack/defense calculations
- Equipment bonuses affect combat effectiveness
- Experience and gold rewards for victories
- Quest progress tracking

### Inventory System
- Collect items from treasures
- Use keys to unlock doors automatically
- Manage equipment and consumables
- Enhanced item display with type and effect information

### Quest System
- Multiple quest types (combat, collection, exploration)
- Dynamic quest completion tracking
- Reward system for completed objectives

### Level Progression
- Find stairs to advance deeper
- Each level is procedurally generated
- Increasing difficulty and rewards

## 🔧 Technical Details

### Performance
- Efficient 2D matrix operations for map access
- Recursive algorithms with depth limiting
- Queue-based action processing
- Difficulty-based content scaling

### Extensibility
- Modular class design for easy feature addition
- Configurable map generation parameters
- Pluggable quest and item systems
- Difficulty-based scaling system

## 🎨 Future Enhancements

- **Save/Load System**: Persist game state between sessions
- **More Items**: Expanded inventory and equipment system
- **Advanced Combat**: Special abilities and status effects
- **Multiplayer**: Turn-based multiplayer support
- **Graphics**: Optional visual representation of the map
- **More Difficulties**: Additional difficulty levels and custom settings

## 📝 License

This project is open source and available under the MIT License.

---

**Happy Dungeon Crawling!** 🗡️⚔️🛡️
