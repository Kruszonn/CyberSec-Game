from __future__ import annotations

import os

import pygame


class AssetCache:
    def __init__(self) -> None:
        self._images: dict[tuple[str, tuple[int, int] | None], pygame.Surface] = {}

    def image(
        self,
        path: str,
        size: tuple[int, int] | None = None,
        fallback_size: tuple[int, int] = (16, 16),
        fallback_color: tuple[int, int, int] = (200, 60, 200),
    ) -> pygame.Surface:
        # Key includes size so we can cache scaled versions.
        key = (path, size)
        cached = self._images.get(key)
        if cached is not None:
            return cached

        surf: pygame.Surface
        if path and os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
        else:
            w, h = fallback_size
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.fill((*fallback_color, 255))
            pygame.draw.rect(surf, (30, 30, 30), pygame.Rect(0, 0, w, h), 2)

        if size is not None:
            sw, sh = size
            if sw > 0 and sh > 0 and (surf.get_width() != sw or surf.get_height() != sh):
                surf = pygame.transform.scale(surf, (sw, sh))

        self._images[key] = surf
        return surf
