from enum import Enum, auto

TILE_SIZE = 52
UI_PANEL_WIDTH = 300
MAX_LEVELS = 5
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


class GameState(Enum):
    LOADING = auto()
    MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    QUIT = auto()

