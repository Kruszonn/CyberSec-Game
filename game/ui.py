from __future__ import annotations

import pygame

from .constants import BLACK, GRAY, LIGHT_GRAY, WHITE, YELLOW


def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    # Minimal wrap (no textwrap dependency)
    words = text.split(" ")
    lines: list[str] = []

    cur = ""
    for w in words:
        if cur == "":
            test = w
        else:
            test = cur + " " + w

        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w

    if cur:
        lines.append(cur)

    return lines


class TextBox:
    def __init__(self, font: pygame.font.Font):
        self.font = font

    def draw(self, screen: pygame.Surface, rect: pygame.Rect, text: str, speaker: str | None = None) -> None:
        pygame.draw.rect(screen, GRAY, rect)
        pygame.draw.rect(screen, LIGHT_GRAY, rect, 2)

        pad = 12
        x = rect.x + pad
        y = rect.y + pad

        if speaker:
            name_surf = self.font.render(speaker, True, YELLOW)
            screen.blit(name_surf, (x, y))
            y += name_surf.get_height() + 6

        max_w = rect.w - pad * 2
        lines = wrap_text(self.font, text, max_w)
        for line in lines[:8]:
            surf = self.font.render(line, True, WHITE)
            screen.blit(surf, (x, y))
            y += surf.get_height() + 4


class ChoiceMenu:
    def __init__(self, font: pygame.font.Font):
        self.font = font

    def draw(self, screen: pygame.Surface, rect: pygame.Rect, choices: list[str], selected: int) -> None:
        pygame.draw.rect(screen, GRAY, rect)
        pygame.draw.rect(screen, LIGHT_GRAY, rect, 2)

        pad = 10
        x = rect.x + pad
        y = rect.y + pad

        for i, label in enumerate(choices):
            prefix = "> " if i == selected else "  "
            color = YELLOW if i == selected else WHITE
            surf = self.font.render(prefix + label, True, color)
            screen.blit(surf, (x, y))
            y += surf.get_height() + 6
