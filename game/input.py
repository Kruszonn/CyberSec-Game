from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class InputState:
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False

    interact_pressed: bool = False  # edge-triggered (KEYDOWN)
    confirm_pressed: bool = False   # edge-triggered (KEYDOWN)
    cancel_pressed: bool = False    # edge-triggered (KEYDOWN)


def build_input_state(events: list[pygame.event.Event]) -> InputState:
    keys = pygame.key.get_pressed()

    st = InputState(
        up=bool(keys[pygame.K_w]),
        down=bool(keys[pygame.K_s]),
        left=bool(keys[pygame.K_a]),
        right=bool(keys[pygame.K_d]),
    )

    for ev in events:
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_e:
                st.interact_pressed = True
            elif ev.key == pygame.K_RETURN:
                st.confirm_pressed = True
            elif ev.key == pygame.K_ESCAPE:
                st.cancel_pressed = True

    return st
