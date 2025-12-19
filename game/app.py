from __future__ import annotations

import pygame

from .constants import FPS, SCREEN_H, SCREEN_W
from .input import build_input_state
from .save_system import default_save, load_save
from .assets import AssetCache
from .scenes import MenuScene


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Anime Security Training")

        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()

        self.input_state = None

        self.save = load_save()

        self.assets = AssetCache()

        self.scene = MenuScene(self)

    def default_save(self) -> dict:
        return default_save()

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    running = False

            self.input_state = build_input_state(events)

            res = self.scene.handle_input(self.input_state, events)
            if res.quit_game:
                running = False
            if res.next_scene is not None:
                self.scene = res.next_scene

            res = self.scene.update(dt)
            if res.quit_game:
                running = False
            if res.next_scene is not None:
                self.scene = res.next_scene

            self.scene.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
