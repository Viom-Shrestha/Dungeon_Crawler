import time

import pygame

from mvc.constants import GameState
from mvc.model import GameModel
from mvc.view import GameView


class DungeonCrawlerController:
    """Controller layer: input handling, event dispatch, and game loop."""

    def __init__(self, difficulty: str = "normal"):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass

        self.model = GameModel(difficulty)
        self.view = GameView(self.model)

    # ---------- Flow ----------
    def _start_new_run(self) -> None:
        self.model.start_new_run()
        self.view.reload_monster_sprites()
        self.view.rebuild_tile_variants()

    def _handle_menu_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.model.state = GameState.QUIT
            return

        for button in self.view.menu_buttons:
            if not button.handle_event(event):
                continue

            if button.text.startswith("Start"):
                self._start_new_run()
            elif button.text.startswith("Difficulty"):
                new_difficulty = self.model.cycle_difficulty()
                button.text = f"Difficulty: {new_difficulty.capitalize()}"
            elif button.text.startswith("Multiplayer"):
                self.model.set_multiplayer(not self.model.multiplayer)
                button.text = f"Multiplayer: {'On' if self.model.multiplayer else 'Off'}"
            elif button.text == "Quit":
                self.model.state = GameState.QUIT

    def _handle_play_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.model.show_inventory or self.model.show_quests:
                    self.model.show_inventory = False
                    self.model.show_quests = False
                else:
                    self.model.state = GameState.MENU

            elif event.key == pygame.K_w:
                self.view.set_actor_direction(1, 0, -1)
                self.model.move_actor(self.model.player, 0, -1)
            elif event.key == pygame.K_s:
                self.view.set_actor_direction(1, 0, 1)
                self.model.move_actor(self.model.player, 0, 1)
            elif event.key == pygame.K_a:
                self.view.set_actor_direction(1, -1, 0)
                self.model.move_actor(self.model.player, -1, 0)
            elif event.key == pygame.K_d:
                self.view.set_actor_direction(1, 1, 0)
                self.model.move_actor(self.model.player, 1, 0)

            elif self.model.multiplayer and event.key == pygame.K_UP:
                self.view.set_actor_direction(2, 0, -1)
                self.model.move_actor(self.model.player2, 0, -1)
            elif self.model.multiplayer and event.key == pygame.K_DOWN:
                self.view.set_actor_direction(2, 0, 1)
                self.model.move_actor(self.model.player2, 0, 1)
            elif self.model.multiplayer and event.key == pygame.K_LEFT:
                self.view.set_actor_direction(2, -1, 0)
                self.model.move_actor(self.model.player2, -1, 0)
            elif self.model.multiplayer and event.key == pygame.K_RIGHT:
                self.view.set_actor_direction(2, 1, 0)
                self.model.move_actor(self.model.player2, 1, 0)

            if event.key == pygame.K_1:
                self.model.set_active_player(1)
            elif event.key == pygame.K_2:
                self.model.set_active_player(2)

        elif event.type == pygame.MOUSEMOTION:
            for button in self.view.play_buttons:
                button.handle_event(event)
            if self.view.quit_button:
                self.view.quit_button.handle_event(event)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for button in self.view.play_buttons:
                    if not button.handle_event(event):
                        continue
                    if button.text == "Inventory":
                        self.model.show_inventory = not self.model.show_inventory
                        self.model.show_quests = False
                    elif button.text == "Quests":
                        self.model.show_quests = not self.model.show_quests
                        self.model.show_inventory = False
                    elif button.text == "Undo":
                        self.model.undo_move()

                if self.view.quit_button and self.view.quit_button.handle_event(event):
                    self._start_new_run()
                    self.model.state = GameState.MENU

                item_index = self.view.inventory_item_index_at(event.pos)
                if item_index is not None:
                    self.model.use_inventory_item(item_index, mouse_button=1)

            elif event.button == 3:
                item_index = self.view.inventory_item_index_at(event.pos)
                if item_index is not None:
                    self.model.use_inventory_item(item_index, mouse_button=3)

            elif event.button == 4:
                self.model.scroll_offset = max(0, self.model.scroll_offset - 20)

            elif event.button == 5:
                max_scroll = self.view.max_inventory_scroll()
                self.model.scroll_offset = min(max_scroll, self.model.scroll_offset + 20)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.model.state = GameState.QUIT
                continue

            if self.model.state == GameState.MENU:
                self._handle_menu_events(event)
            elif self.model.state == GameState.PLAYING:
                self._handle_play_events(event)
            elif self.model.state in (GameState.GAME_OVER, GameState.VICTORY):
                if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                    self.model.state = GameState.MENU

    # ---------- Main loop ----------
    def run(self) -> None:
        while True:
            self._handle_events()
            if self.model.state == GameState.QUIT:
                break

            if self.model.state == GameState.LOADING:
                self.view.draw_loading()
                if time.time() - self.model.loading_start >= self.model.loading_duration:
                    pygame.display.flip()
                    pygame.time.delay(1000)
                    self.model.state = GameState.MENU

            elif self.model.state == GameState.MENU:
                self.view.draw_menu()

            elif self.model.state == GameState.PLAYING:
                if not self.model.player.is_alive() and (not self.model.multiplayer or not self.model.player2.is_alive()):
                    self.model.state = GameState.GAME_OVER
                    self.view.draw_game_over()
                else:
                    self.view.draw_playing()

            elif self.model.state == GameState.GAME_OVER:
                self.view.draw_game_over()

            elif self.model.state == GameState.VICTORY:
                self.view.draw_victory()

            pygame.display.flip()
            self.view.clock.tick(60)

        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        pygame.quit()


def main() -> None:
    controller = DungeonCrawlerController("normal")
    controller.run()


if __name__ == "__main__":
    main()

