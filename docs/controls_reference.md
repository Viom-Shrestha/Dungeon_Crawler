# Dungeon Crawler Controls and Commands

## Scope
- This document describes all runtime inputs in the current GUI implementation (`src/mvc/controller.py`).
- There is no in-game typed command console in the current `src/` version. Input is keyboard and mouse only.

## Global
- Window close button (`pygame.QUIT`): exit game.

## Main Menu State
- `Esc`: quit game.
- Mouse move: button hover highlight.
- Left click `Start Game`: start a new run.
- Left click `Difficulty: ...`: cycle difficulty (`Easy -> Normal -> Hard -> Easy`).
- Left click `Multiplayer: On/Off`: toggle multiplayer mode.
- Left click `Quit`: quit game.

## Playing State (Keyboard)
- `W`: move P1 up.
- `A`: move P1 left.
- `S`: move P1 down.
- `D`: move P1 right.
- `Up Arrow`: move P2 up (multiplayer only).
- `Left Arrow`: move P2 left (multiplayer only).
- `Down Arrow`: move P2 down (multiplayer only).
- `Right Arrow`: move P2 right (multiplayer only).
- `Esc`: close inventory/quests if open; otherwise return to menu.
- `1`: set active inventory target to P1.
- `2`: set active inventory target to P2 (multiplayer only).

## Playing State (Mouse)
- Mouse move: hover highlight on in-game buttons.
- Left click `Inventory`: toggle inventory panel (and close quests panel).
- Left click `Quests`: toggle quests panel (and close inventory panel).
- Left click `Undo`: undo last stored move for P1.
- Left click bottom-right `Quit`: reset run and return to menu.
- Left click inventory item row: use/equip selected item on active target player.
- Right click inventory item row: sell selected item from shared inventory (gold goes to active target player).
- Mouse wheel up: scroll inventory list up.
- Mouse wheel down: scroll inventory list down.

## Game Over / Victory States
- Any key press: return to main menu.
- Left click: return to main menu.

