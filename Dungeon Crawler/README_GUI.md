# Dungeon Crawler - GUI Version

A modern, Pygame-based graphical user interface for the Dungeon Crawler game!

## Features

### 🎮 **Visual Gameplay**
- **Tile-based map rendering** with color-coded elements
- **Smooth animations** and transitions
- **Real-time updates** of player position and game state

### 🖱️ **Multiple Control Methods**
- **Mouse controls** for buttons and UI elements
- **Keyboard shortcuts** for quick actions
- **Arrow keys** and WASD for movement

### 🎨 **Modern UI Design**
- **Right-side status panel** showing player stats, health bar, and level info
- **Bottom control buttons** for movement and actions
- **Message log** displaying game events and combat results
- **Clean, intuitive interface** with hover effects

### 🗺️ **Enhanced Map Visualization**
- **Fog of war** system with revealed areas
- **Color-coded tiles**:
  - 🟫 Brown: Walls
  - 🟡 Yellow: Treasures
  - 🔴 Red: Monsters
  - 🟣 Purple: Stairs
  - 🟦 Blue: Player
  - 🟨 Gold: Doors
  - ⚪ Light Gray: Empty spaces
  - ⚫ Dark Gray: Unexplored areas

## Installation

### Prerequisites
- Python 3.7 or higher
- Pygame 2.5.0 or higher

### Quick Install
```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install Pygame directly
pip install pygame
```

### Manual Install
```bash
pip install pygame
```

## How to Play

### 🚀 **Starting the Game**
```bash
# Use the launcher (recommended)
python launcher.py

# Or run GUI version directly
python dungeon_crawler_gui.py
```

### 🎯 **Controls**

#### **Movement**
- **Arrow Keys** or **WASD**: Move player
- **Mouse**: Click movement buttons
- **Movement Buttons**: Click ↑↓←→ buttons

#### **Actions**
- **I**: Toggle inventory
- **Q**: Toggle quests
- **Z**: Undo last move
- **ESC**: Close open panels

#### **Mouse Controls**
- **Left Click**: Interact with buttons
- **Hover**: See button effects
- **Click and drag**: Not implemented (future feature)

### 🎮 **Gameplay Features**

#### **Combat System**
- **Automatic combat** when encountering monsters
- **Real-time damage calculation**
- **Experience and gold rewards**
- **Quest progress tracking**

#### **Inventory Management**
- **Visual item display**
- **Equipment system** (weapons and armor)
- **Consumable items** (potions)
- **Key management** for doors

#### **Quest System**
- **Multiple active quests**
- **Progress tracking**
- **Reward information**
- **Completion status**

## File Structure

```
Dungeon Crawler/
├── dungeon_crawler.py          # Original text-based version
├── dungeon_crawler_gui.py      # New Pygame GUI version
├── launcher.py                 # Game launcher (choose version)
├── requirements.txt            # Dependencies
├── README.md                   # Original documentation
└── README_GUI.md              # This file
```

## Technical Details

### **Screen Resolution**
- **Width**: 1200 pixels
- **Height**: 800 pixels
- **Tile Size**: 32x32 pixels

### **Performance**
- **Target FPS**: 60 FPS
- **Smooth rendering** with Pygame's optimized graphics
- **Efficient tile rendering** system

### **Memory Management**
- **Optimized sprite rendering**
- **Efficient UI updates**
- **Minimal memory footprint**

## Troubleshooting

### **Common Issues**

#### **Pygame Not Found**
```bash
# Error: No module named 'pygame'
pip install pygame
```

#### **Display Issues**
- Ensure your graphics drivers are up to date
- Try running in windowed mode
- Check screen resolution compatibility

#### **Performance Issues**
- Close other applications
- Reduce screen resolution if needed
- Update Pygame to latest version

### **Error Messages**

#### **"Could not import dungeon_crawler_gui module"**
- Ensure all files are in the same directory
- Check Python version compatibility
- Verify file permissions

#### **"Pygame error: No available video device"**
- Update graphics drivers
- Try running on different display
- Check virtual environment settings

## Future Enhancements

### **Planned Features**
- [ ] **Sprite-based graphics** instead of colored rectangles
- [ ] **Sound effects** and background music
- [ ] **Particle effects** for combat and magic
- [ ] **Save/load system** for game progress
- [ ] **Multiple difficulty levels** with visual indicators
- [ ] **Mini-map** for better navigation
- [ ] **Character customization** options

### **UI Improvements**
- [ ] **Draggable panels** for custom layouts
- [ ] **Tooltips** for better item information
- [ ] **Context menus** for advanced actions
- [ ] **Keyboard shortcuts** customization
- [ ] **Theme selection** (light/dark modes)

## Contributing

### **Development Setup**
1. Fork the repository
2. Install development dependencies
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### **Code Style**
- Follow PEP 8 guidelines
- Add type hints where appropriate
- Include docstrings for new functions
- Test with multiple Python versions

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Support

If you encounter issues or have suggestions:
1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with detailed information
4. Include system information and error messages

---

**Enjoy your dungeon crawling adventure with beautiful graphics!** 🎮⚔️🏰
