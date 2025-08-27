# 🐉 Dungeon Crawler

A Python dungeon crawler game with **two play modes**:  
- **CLI** (Command-Line Interface) for a retro text-based adventure.  
- **GUI** (Graphical Interface with Pygame) for a modern experience.  

Choose how you want to play from `launcher.py`.  

---

## 📂 Project Structure  

```
Dungeon-Crawler/
│
├── assets/                     # Sprites, sounds, UI, etc.
├── src/                        # All Python source files
│   ├── dungeon_crawler.py      # CLI game logic
│   ├── dungeon_crawler_gui.py  # GUI game (pygame)
│   |__ launcher.py             # Entry point (choose CLI or GUI)
│   
├── highscore.txt
├── requirements.txt
├── LICENSE
├── README.md
└── .gitignore
```

---

## 🚀 Getting Started  

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/dungeon-crawler.git
cd dungeon-crawler
```

### 2. Install dependencies  
Make sure you have Python 3.9+ installed.  
Then install requirements:  

```bash
pip install -r requirements.txt
```

Dependencies include:  
- `pygame` (for GUI mode)  

### 3. Run the launcher  
```bash
python src/launcher.py
```

You’ll be prompted to choose:  
```
1. CLI Mode
2. GUI Mode
```

---

## 🎮 Gameplay  

### CLI Mode
- Explore the dungeon via text commands.  
- Fog of war map display in ASCII.  
- Commands include:  
  - Movement: `north` / `south` / `east` / `west` (or `w/s/d/a`)  
  - Items: `use <item>`, `inventory`  
  - Player info: `status`, `quests`  
  - Undo last move: `undo`  
  - `quit` to exit  

### GUI Mode  
- Grid-based movement with visible sprites.  
- Click-based inventory management.  
- Monster sprites, treasure chests, stairs, and fog of war.  
- Quest rewards, multiple items, consumables, and equipment.  
- Multiplayer toggle available in the main menu.  

---

## ⚔️ Features  

- Procedural map generation with difficulty scaling.  
- Quests (kill monsters, collect treasures, defeat the dragon boss).  
- Inventory system with weapons, armor, and consumables.  
- Combat system with attack, defense, health, and XP.  
- Quest rewards (gold, experience, and items).  
- Fog of war exploration.  
- Undo/redo system (CLI).  
- Multiplayer option (GUI).  

---

## 🎨 Assets  

Place sprites, and sound effects in the `assets/` folder.  
- Monsters: `assets/monsters/*.png`  


## 📝 License  

MIT License – free to use and modify.  

---

✨ Have fun exploring the dungeon, whether through **retro text** or **modern GUI**!
