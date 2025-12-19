from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass

import pygame

from .constants import (
    GREEN,
    PLAYER_SPEED,
    PLAYER_W,
    PLAYER_H,
    PORTRAIT_BOX_H,
    PORTRAIT_BOX_PAD,
    PORTRAIT_BOX_W,
    RED,
    SCREEN_H,
    SCREEN_W,
    TILE_SIZE,
    UI_FONT_SIZE,
    UI_TEXTBOX_H,
    WHITE,
    YELLOW,
)
from .input import InputState
from .save_system import load_save, save_game
from .tiled import TiledMap
from .ui import ChoiceMenu, TextBox
from .assets import AssetCache


def clamp(v: float, lo: float, hi: float) -> float:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def dist_sq(ax: float, ay: float, bx: float, by: float) -> float:
    dx = ax - bx
    dy = ay - by
    return dx * dx + dy * dy


@dataclass
class SceneResult:
    next_scene: "BaseScene | None" = None
    quit_game: bool = False


class BaseScene:
    def __init__(self, app: "App"):
        self.app = app

    def handle_input(self, st: InputState, events: list[pygame.event.Event]) -> SceneResult:
        return SceneResult()

    def update(self, dt: float) -> SceneResult:
        return SceneResult()

    def draw(self, screen: pygame.Surface) -> None:
        raise NotImplementedError


class MenuScene(BaseScene):
    def __init__(self, app: "App"):
        super().__init__(app)
        self.font = pygame.font.Font(None, 40)
        self.small = pygame.font.Font(None, 26)
        self.options = ["New Game", "Load Game", "Quit"]
        self.sel = 0

    def handle_input(self, st: InputState, events: list[pygame.event.Event]) -> SceneResult:
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    self.sel = (self.sel - 1) % len(self.options)
                elif ev.key == pygame.K_DOWN:
                    self.sel = (self.sel + 1) % len(self.options)

        if st.confirm_pressed:
            if self.sel == 0:
                self.app.save = self.app.default_save()
                save_game(self.app.save)
                return SceneResult(next_scene=WorldScene(self.app))
            if self.sel == 1:
                self.app.save = load_save()
                return SceneResult(next_scene=WorldScene(self.app))
            if self.sel == 2:
                return SceneResult(quit_game=True)

        return SceneResult()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((18, 18, 28))
        title = self.font.render("Anime Security Training", True, WHITE)
        screen.blit(title, (60, 60))

        y = 160
        for i, opt in enumerate(self.options):
            color = YELLOW if i == self.sel else WHITE
            label = self.small.render(("> " if i == self.sel else "  ") + opt, True, color)
            screen.blit(label, (80, y))
            y += 40

        hint = self.small.render("WASD move, E interact, Enter confirm, Esc quit", True, (180, 180, 180))
        screen.blit(hint, (60, SCREEN_H - 50))


class GeneratedMap:
    """Fallback dev map(s) (so the scaffold runs before you export from Tiled)."""

    def __init__(self, map_id: str, width_tiles: int = 160, height_tiles: int = 120):
        self.map_id = map_id

        self.default_zoom = 1.0
        if map_id != "city":
            width_tiles = 60
            height_tiles = 45
            self.default_zoom = 1.6

        self.width = width_tiles
        self.height = height_tiles
        self.tile_w = TILE_SIZE
        self.tile_h = TILE_SIZE
        self.pixel_w = self.width * self.tile_w
        self.pixel_h = self.height * self.tile_h

        self.colliders: list[pygame.Rect] = []
        wpx = self.pixel_w
        hpx = self.pixel_h
        self.colliders.append(pygame.Rect(0, 0, wpx, 16))
        self.colliders.append(pygame.Rect(0, hpx - 16, wpx, 16))
        self.colliders.append(pygame.Rect(0, 0, 16, hpx))
        self.colliders.append(pygame.Rect(wpx - 16, 0, 16, hpx))

        self.portals: list[dict] = []
        self.books: list[dict] = []
        self.decorations: list[dict] = []
        self.background_sprite: str | None = None

        if map_id == "city":
            self.background_sprite = os.path.join("assets", "tiles", "city_bg.png")

            b1 = pygame.Rect(400, 260, 220, 160)
            b2 = pygame.Rect(900, 520, 260, 190)
            self.colliders.append(b1)
            self.colliders.append(b2)

            self.decorations.append({"rect": b1, "sprite": os.path.join("assets", "tiles", "house_a.png")})
            self.decorations.append({"rect": b2, "sprite": os.path.join("assets", "tiles", "house_b.png")})

            self.npcs = [
                {
                    "npc_id": "aya",
                    "dialogue": os.path.join("data", "dialogues", "npc_aya.json"),
                    "rect": pygame.Rect(320, 220, 18, 22),
                    "sprite": os.path.join("assets", "sprites", "npc_aya.png"),
                },
                {
                    "npc_id": "mika",
                    "dialogue": os.path.join("data", "dialogues", "npc_mika.json"),
                    "rect": pygame.Rect(1050, 320, 18, 22),
                    "sprite": os.path.join("assets", "sprites", "npc_mika.png"),
                },
            ]

            self.portals.append(
                {
                    "rect": pygame.Rect(600, 420, 22, 18),
                    "target_map": "house_1",
                    "target_x": 240.0,
                    "target_y": 300.0,
                    "target_zoom": 1.6,
                    "prompt": "Press E to enter",
                    "sprite": os.path.join("assets", "sprites", "door.png"),
                }
                   
            )
            #self.portals.append(
             #   {
              #      "rect": pygame.Rect(1100, 700, 22, 18),
               #     "target_map": "house_2",
                #    "target_x": 240.0,
                 #   "target_y": 300.0,
                  #  "target_zoom": 1.6,
                   # "prompt": "Press E to enter",
                    #"sprite": os.path.join("assets", "sprites", "door.png"),
                #}
            #)
        
        elif map_id == "house_1":
            self.background_sprite = os.path.join("assets", "tiles", "house_1_bg.png")

            self.npcs = [
                {
                    "npc_id": "ren",
                    "dialogue": os.path.join("data", "dialogues", "npc_ren.json"),
                    "rect": pygame.Rect(280, 200, 18, 22),
                    "sprite": os.path.join("assets", "sprites", "npc_ren.png"),
                }
            ]

            self.books = [
                {
                    "rect": pygame.Rect(420, 190, 18, 18),
                    "title": "Phishing Basics",
                    "text": "Phishing to metoda oszustwa, w której cyberprzestępcy podszywają się pod zaufane osoby lub instytucje, np. banki czy serwisy społecznościowe. Celem jest wyłudzenie poufnych informacji, takich jak hasła, dane kart kredytowych czy login do konta. Phishing może przybierać formę fałszywych e-maili, SMS-ów, a nawet wiadomości w mediach społecznościowych. Najlepszą ochroną jest ostrożność, sprawdzanie adresów URL i nigdy nieklikanie podejrzanych linków.",
                    "prompt": "Press E to read: Phishing Basics",
                    "sprite": os.path.join("assets", "sprites", "book.png"),
                },
                {
                    "rect": pygame.Rect(520, 250, 18, 18),
                    "title": "Passwords & Passphrases",
                    "text": "Hasła to Twoja pierwsza linia obrony w świecie cyfrowym. Silne hasło powinno być długie, unikalne i zawierać kombinację liter, cyfr i znaków specjalnych. Unikaj łatwych haseł typu „123456” lub „password” oraz używania tego samego hasła w wielu serwisach. Dobrym rozwiązaniem jest menedżer haseł, który pozwala bezpiecznie przechowywać i generować skomplikowane hasła.",
                    "prompt": "Press E to read: Passwords",
                    "sprite": os.path.join("assets", "sprites", "book.png"),
                },
                {
                    "rect": pygame.Rect(600, 310, 18, 18),
                    "title": "MFA Tips",
                    "text": "MFA, czyli uwierzytelnianie wieloskładnikowe, dodaje dodatkową warstwę ochrony do Twoich kont. Oprócz hasła, wymaga np. kodów SMS, aplikacji uwierzytelniającej (Authenticator) lub biometrii. Dzięki MFA, nawet jeśli ktoś pozna Twoje hasło, nie będzie mógł zalogować się bez dodatkowego czynnika. To prosta i skuteczna metoda zwiększenia bezpieczeństwa kont online.",
                    "sprite": os.path.join("assets", "sprites", "book.png"),
                },
            ]

            self.portals.append(
                {
                    "rect": pygame.Rect(220, self.pixel_h - 60, 140, 34),
                    "target_map": "city",
                    "target_x": 500.0,
                    "target_y": 450.0,
                    "target_zoom": 1.0,
                    "prompt": "Press E to exit",
                    "sprite": os.path.join("assets", "sprites", "door.png"),
                }
            )
        #elif map_id == "house_2":
        #    self.background_sprite = os.path.join("assets", "tiles", "house_2_bg.png")



    def world_bounds_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.pixel_w, self.pixel_h)

    def draw(self, screen: pygame.Surface, camera_x: float, camera_y: float, assets: AssetCache) -> None:
        if self.background_sprite:
            bg = assets.image(self.background_sprite, fallback_size=(self.pixel_w, self.pixel_h), fallback_color=(30, 50, 40))
            screen.blit(bg, (-camera_x, -camera_y))
        else:
            screen.fill((30, 50, 40))

        # fallback subtle checker overlay if you want to see movement even with bg missing
        sw, sh = screen.get_size()
        start_x = int(camera_x // self.tile_w)
        start_y = int(camera_y // self.tile_h)
        end_x = int((camera_x + sw) // self.tile_w) + 1
        end_y = int((camera_y + sh) // self.tile_h) + 1
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(self.width, end_x)
        end_y = min(self.height, end_y)

        for ty in range(start_y, end_y):
            for tx in range(start_x, end_x):
                px = tx * self.tile_w - camera_x
                py = ty * self.tile_h - camera_y
                c = (34, 56, 44) if ((tx + ty) & 1) == 0 else (32, 52, 42)
                pygame.draw.rect(screen, c, pygame.Rect(int(px), int(py), self.tile_w, self.tile_h))

        for d in self.decorations:
            r: pygame.Rect = d["rect"]
            sp = str(d.get("sprite", ""))
            img = assets.image(sp, size=(r.w, r.h), fallback_size=(r.w, r.h), fallback_color=(70, 70, 95))
            screen.blit(img, (int(r.x - camera_x), int(r.y - camera_y)))
        
        


class WorldScene(BaseScene):
    def __init__(
        self,
        app: "App",
        map_id: str | None = None,
        spawn_xy: tuple[float, float] | None = None,
        zoom: float | None = None,
    ):
        super().__init__(app)

        self.font = pygame.font.Font(None, UI_FONT_SIZE)
        self.save = app.save

        if map_id is None:
            map_id = str(self.save.get("world", {}).get("map", "city"))
        self.map_id = map_id
        self.save.setdefault("world", {})["map"] = self.map_id

        self.map_path = os.path.join("data", "maps", f"{self.map_id}.json")
        self.tiled: TiledMap | None = None
        self.gen: GeneratedMap | None = None

        if os.path.exists(self.map_path):
            self.tiled = TiledMap(self.map_path)
        else:
            self.gen = GeneratedMap(self.map_id)

        if spawn_xy is not None:
            px, py = spawn_xy
        else:
            px = float(self.save["player"]["x"])
            py = float(self.save["player"]["y"])

        self.player = pygame.Rect(int(px), int(py), PLAYER_W, PLAYER_H)

        self.zoom = float(zoom) if zoom is not None else self._map_default_zoom()
        self.zoom = clamp(self.zoom, 1.0, 2.5)

        self.camera_x = 0.0
        self.camera_y = 0.0
        self._view_surface: pygame.Surface | None = None
        self._view_size: tuple[int, int] = (0, 0)

        self.near_npc_label: str | None = None
        self.near_portal_label: str | None = None
        self.near_book_label: str | None = None

    def _map_default_zoom(self) -> float:
        if self.tiled:
            try:
                return float(self.tiled.properties.get("default_zoom", 1.0))
            except Exception:
                return 1.0
        assert self.gen is not None
        return float(getattr(self.gen, "default_zoom", 1.0))

    def _world_bounds(self) -> pygame.Rect:
        if self.tiled:
            return self.tiled.world_bounds_rect()
        assert self.gen is not None
        return self.gen.world_bounds_rect()

    def _colliders(self) -> list[pygame.Rect]:
        if self.tiled:
            return self.tiled.colliders
        assert self.gen is not None
        return self.gen.colliders

    def _npcs(self) -> list[dict]:
        if self.tiled:
            out: list[dict] = []
            for npc in self.tiled.npcs:
                npc_id = str(npc.properties.get("npc_id", npc.name))
                dialogue = npc.properties.get("dialogue")
                rect = pygame.Rect(int(npc.x), int(npc.y), max(10, int(npc.w)), max(10, int(npc.h)))
                sprite = npc.properties.get("sprite")
                out.append({"npc_id": npc_id, "dialogue": dialogue, "rect": rect, "sprite": sprite})
            return out
        assert self.gen is not None
        return self.gen.npcs

    def _portals(self) -> list[dict]:
        if self.tiled:
            out: list[dict] = []
            for p in self.tiled.portals:
                rect = pygame.Rect(int(p.x), int(p.y), max(10, int(p.w)), max(10, int(p.h)))
                out.append({"rect": rect, **p.properties})
            return out
        assert self.gen is not None
        return getattr(self.gen, "portals", [])

    def _books(self) -> list[dict]:
        if self.tiled:
            out: list[dict] = []
            for b in self.tiled.books:
                rect = pygame.Rect(int(b.x), int(b.y), max(10, int(b.w)), max(10, int(b.h)))
                props = dict(b.properties)
                props["rect"] = rect
                out.append(props)
            return out
        assert self.gen is not None
        return getattr(self.gen, "books", [])

    def handle_input(self, st: InputState, events: list[pygame.event.Event]) -> SceneResult:
        if st.cancel_pressed:
            self.save["player"]["x"] = float(self.player.x)
            self.save["player"]["y"] = float(self.player.y)
            save_game(self.save)
            return SceneResult(next_scene=MenuScene(self.app))

        self.near_npc_label = None
        self.near_portal_label = None
        self.near_book_label = None

        nearest = self._nearest_interactable()
        if nearest is None:
            return SceneResult()

        kind = nearest["kind"]
        data = nearest["data"]

        if kind == "npc":
            self.near_npc_label = f"Press E to talk to {data['npc_id']}"
            if st.interact_pressed:
                dpath = data.get("dialogue") or os.path.join("data", "dialogues", "npc_aya.json")
                return SceneResult(next_scene=DialogueScene(self.app, return_scene=self, dialogue_path=dpath, npc_id=data["npc_id"]))
            return SceneResult()

        if kind == "portal":
            prompt = data.get("prompt") or ("Press E to enter" if self.map_id == "city" else "Press E to exit")
            self.near_portal_label = str(prompt)

            if st.interact_pressed:
                target_map = str(data.get("target_map", ""))
                try:
                    tx = float(data.get("target_x", self.player.x))
                    ty = float(data.get("target_y", self.player.y))
                except Exception:
                    tx, ty = float(self.player.x), float(self.player.y)

                z = None
                tzoom = data.get("target_zoom")
                if tzoom is not None:
                    try:
                        z = float(tzoom)
                    except Exception:
                        z = None

                if target_map:
                    self.save["player"]["x"] = float(self.player.x)
                    self.save["player"]["y"] = float(self.player.y)
                    save_game(self.save)
                    return SceneResult(next_scene=WorldScene(self.app, map_id=target_map, spawn_xy=(tx, ty), zoom=z))
            return SceneResult()

        if kind == "book":
            title = str(data.get("title", "Book"))
            text = str(data.get("text", ""))
            prompt = data.get("prompt") or "Press E to read"
            self.near_book_label = str(prompt)
            if st.interact_pressed:
                return SceneResult(next_scene=InfoScene(self.app, return_scene=self, title=title, text=text))
            return SceneResult()

        return SceneResult()

    def update(self, dt: float) -> SceneResult:
        st = self.app.input_state

        vx = 0.0
        vy = 0.0
        if st.left:
            vx -= 1.0
        if st.right:
            vx += 1.0
        if st.up:
            vy -= 1.0
        if st.down:
            vy += 1.0

        if vx != 0.0 and vy != 0.0:
            inv = 1.0 / math.sqrt(2.0)
            vx *= inv
            vy *= inv

        dx = vx * PLAYER_SPEED * dt
        dy = vy * PLAYER_SPEED * dt

        self._move_and_collide(dx, 0.0)
        self._move_and_collide(0.0, dy)

        bounds = self._world_bounds()
        view_w = int(SCREEN_W / self.zoom)
        view_h = int(SCREEN_H / self.zoom)
        view_w = max(160, view_w)
        view_h = max(120, view_h)

        target_x = (self.player.x + self.player.w * 0.5) - view_w * 0.5
        target_y = (self.player.y + self.player.h * 0.5) - view_h * 0.5

        max_cx = max(0.0, float(bounds.w - view_w))
        max_cy = max(0.0, float(bounds.h - view_h))

        self.camera_x = clamp(target_x, 0.0, max_cx)
        self.camera_y = clamp(target_y, 0.0, max_cy)

        self.save.setdefault("world", {})["map"] = self.map_id
        self.save["player"]["x"] = float(self.player.x)
        self.save["player"]["y"] = float(self.player.y)

        return SceneResult()

    def _move_and_collide(self, dx: float, dy: float) -> None:
        if dx == 0.0 and dy == 0.0:
            return

        self.player.x += int(dx)
        self.player.y += int(dy)

        bounds = self._world_bounds()
        self.player.x = int(clamp(float(self.player.x), 0.0, float(bounds.w - self.player.w)))
        self.player.y = int(clamp(float(self.player.y), 0.0, float(bounds.h - self.player.h)))

        for c in self._colliders():
            if self.player.colliderect(c):
                if dx > 0:
                    self.player.right = c.left
                elif dx < 0:
                    self.player.left = c.right
                if dy > 0:
                    self.player.bottom = c.top
                elif dy < 0:
                    self.player.top = c.bottom

    def _closest_npc(self, max_dist: float) -> dict | None:
        px = self.player.centerx
        py = self.player.centery
        best = None
        best_d = max_dist * max_dist
        for npc in self._npcs():
            r: pygame.Rect = npc["rect"]
            d = dist_sq(px, py, r.centerx, r.centery)
            if d <= best_d:
                best_d = d
                best = npc
        return best

    def _closest_portal(self, max_dist: float) -> dict | None:
        px = self.player.centerx
        py = self.player.centery
        best = None
        best_d = max_dist * max_dist
        for p in self._portals():
            r: pygame.Rect = p["rect"]
            if self.player.colliderect(r):
                return p
            d = dist_sq(px, py, r.centerx, r.centery)
            if d <= best_d:
                best_d = d
                best = p
        return best

    def _closest_book(self, max_dist: float) -> dict | None:
        px = self.player.centerx
        py = self.player.centery
        best = None
        best_d = max_dist * max_dist
        for b in self._books():
            r: pygame.Rect = b["rect"]
            if self.player.colliderect(r):
                return b
            d = dist_sq(px, py, r.centerx, r.centery)
            if d <= best_d:
                best_d = d
                best = b
        return best

    def _nearest_interactable(self) -> dict | None:
        px = self.player.centerx
        py = self.player.centery
        best: dict | None = None
        best_d = 999999999.0

        npc = self._closest_npc(max_dist=48.0)
        if npc is not None:
            r: pygame.Rect = npc["rect"]
            d = dist_sq(px, py, r.centerx, r.centery)
            best = {"kind": "npc", "data": npc, "dist": d}
            best_d = d

        portal = self._closest_portal(max_dist=70.0)
        if portal is not None:
            r: pygame.Rect = portal["rect"]
            d = 0.0 if self.player.colliderect(r) else dist_sq(px, py, r.centerx, r.centery)
            if d < best_d:
                best = {"kind": "portal", "data": portal, "dist": d}
                best_d = d

        book = self._closest_book(max_dist=60.0)
        if book is not None:
            r: pygame.Rect = book["rect"]
            d = 0.0 if self.player.colliderect(r) else dist_sq(px, py, r.centerx, r.centery)
            if d < best_d:
                best = {"kind": "book", "data": book, "dist": d}
                best_d = d

        return best

    def draw(self, screen: pygame.Surface) -> None:
        view_w = max(160, int(SCREEN_W / self.zoom))
        view_h = max(120, int(SCREEN_H / self.zoom))

        if self._view_surface is None or self._view_size != (view_w, view_h):
            self._view_surface = pygame.Surface((view_w, view_h))
            self._view_size = (view_w, view_h)

        view = self._view_surface
        assert view is not None

        if self.tiled:
            view.fill((20, 25, 35))
            self.tiled.draw(view, self.camera_x, self.camera_y)
        else:
            assert self.gen is not None
            self.gen.draw(view, self.camera_x, self.camera_y, self.app.assets)

        # Portals
        for p in self._portals():
            r: pygame.Rect = p["rect"]
            rr = pygame.Rect(int(r.x - self.camera_x), int(r.y - self.camera_y), r.w, r.h)
            sp = str(p.get("sprite", os.path.join("assets", "sprites", "door.png")))
            img = self.app.assets.image(sp, size=(rr.w, rr.h), fallback_size=(rr.w, rr.h), fallback_color=(160, 120, 255))
            view.blit(img, (rr.x, rr.y))

        # Books
        for b in self._books():
            r: pygame.Rect = b["rect"]
            rr = pygame.Rect(int(r.x - self.camera_x), int(r.y - self.camera_y), r.w, r.h)
            sp = str(b.get("sprite", os.path.join("assets", "sprites", "book.png")))
            img = self.app.assets.image(sp, size=(rr.w, rr.h), fallback_size=(rr.w, rr.h), fallback_color=(255, 210, 120))
            view.blit(img, (rr.x, rr.y))

        # NPCs
        for npc in self._npcs():
            r: pygame.Rect = npc["rect"]
            rr = pygame.Rect(int(r.x - self.camera_x), int(r.y - self.camera_y), r.w, r.h)
            sp = str(npc.get("sprite", os.path.join("assets", "sprites", "npc.png")))
            img = self.app.assets.image(sp, size=(rr.w, rr.h), fallback_size=(rr.w, rr.h), fallback_color=(60, 140, 255))
            view.blit(img, (rr.x, rr.y))

        # Player
        pr = pygame.Rect(int(self.player.x - self.camera_x), int(self.player.y - self.camera_y), self.player.w, self.player.h)
        pimg = self.app.assets.image(os.path.join("assets", "sprites", "player.png"), size=(pr.w, pr.h), fallback_size=(pr.w, pr.h), fallback_color=(240, 120, 140))
        view.blit(pimg, (pr.x, pr.y))

        if self.zoom != 1.0:
            scaled = pygame.transform.scale(view, (SCREEN_W, SCREEN_H))
            screen.blit(scaled, (0, 0))
        else:
            screen.blit(view, (0, 0))

        if self.near_npc_label:
            screen.blit(self.font.render(self.near_npc_label, True, WHITE), (12, 12))
        elif self.near_book_label:
            screen.blit(self.font.render(self.near_book_label, True, WHITE), (12, 12))
        elif self.near_portal_label:
            screen.blit(self.font.render(self.near_portal_label, True, WHITE), (12, 12))


class InfoScene(BaseScene):
    def __init__(self, app: "App", return_scene: BaseScene, title: str, text: str):
        super().__init__(app)
        self.return_scene = return_scene
        self.title = title
        self.text = text

        self.font = pygame.font.Font(None, 30)
        self.small = pygame.font.Font(None, UI_FONT_SIZE)
        self.textbox = TextBox(self.small)

    def handle_input(self, st: InputState, events: list[pygame.event.Event]) -> SceneResult:
        if st.cancel_pressed or st.confirm_pressed or st.interact_pressed:
            return SceneResult(next_scene=self.return_scene)
        return SceneResult()

    def draw(self, screen: pygame.Surface) -> None:
        self.return_scene.draw(screen)

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        rect = pygame.Rect(80, 80, SCREEN_W - 160, SCREEN_H - 160)
        pygame.draw.rect(screen, (28, 28, 40), rect)
        pygame.draw.rect(screen, (70, 70, 90), rect, 2)

        title_surf = self.font.render(self.title, True, YELLOW)
        screen.blit(title_surf, (rect.x + 18, rect.y + 16))

        body_rect = pygame.Rect(rect.x + 16, rect.y + 64, rect.w - 32, rect.h - 96)
        self.textbox.draw(screen, body_rect, text=self.text, speaker=None)

        hint = self.small.render("Enter/E/Esc to close", True, (200, 200, 200))
        screen.blit(hint, (rect.x + 18, rect.bottom - 28))


class DialogueScene(BaseScene):
    def __init__(self, app: "App", return_scene: BaseScene, dialogue_path: str, npc_id: str):
        super().__init__(app)
        self.return_scene = return_scene
        self.dialogue_path = dialogue_path
        self.npc_id = npc_id

        self.font = pygame.font.Font(None, UI_FONT_SIZE)
        self.textbox = TextBox(self.font)
        self.choice_menu = ChoiceMenu(self.font)

        self.data = self._load_dialogue(dialogue_path)
        self.nodes = self.data.get("nodes", {})
        self.node_id = self.data.get("start_node", "intro")

        self.selected_choice = 0
        self.portrait_cache: dict[str, pygame.Surface] = {}
        self.portrait_anim_cache: dict[str, tuple[list[pygame.Surface], float]] = {}
        self.portrait_anim_time = 0.0

    def _load_dialogue(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def update(self, dt: float) -> SceneResult:
        self.portrait_anim_time += dt
        return SceneResult()

    def handle_input(self, st: InputState, events: list[pygame.event.Event]) -> SceneResult:
        if st.cancel_pressed:
            save_game(self.app.save)
            return SceneResult(next_scene=self.return_scene)

        node = self.nodes.get(self.node_id, {})
        choices = node.get("choices")

        if isinstance(choices, list) and choices:
            for ev in events:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_UP:
                        self.selected_choice -= 1
                    elif ev.key == pygame.K_DOWN:
                        self.selected_choice += 1

            if self.selected_choice < 0:
                self.selected_choice = 0
            if self.selected_choice >= len(choices):
                self.selected_choice = len(choices) - 1

            if st.confirm_pressed:
                choice = choices[self.selected_choice]
                trust_delta = int(choice.get("trust_delta", 0))
                trust = self.app.save.setdefault("trust", {})
                trust[self.npc_id] = int(trust.get(self.npc_id, 0)) + trust_delta
                
                nxt = choice.get("next")
                if nxt:
                    self.node_id = str(nxt)
                    self.selected_choice = 0
                    return SceneResult()
                
                
                
        else:
            if st.confirm_pressed:
                nxt = node.get("next")
                if nxt:
                    self.node_id = str(nxt)
                    return SceneResult()
            

        action = node.get("action")
        if isinstance(action, dict) and action.get("type") == "start_challenge":
            ch_set = str(action.get("challenge_set", ""))
            if ch_set:
                save_game(self.app.save)
                return SceneResult(next_scene=ChallengeScene(self.app, return_scene=self.return_scene, challenge_set_id=ch_set))

        if not node:
            save_game(self.app.save)
            return SceneResult(next_scene=self.return_scene)

        return SceneResult()

    def draw(self, screen: pygame.Surface) -> None:
        self.return_scene.draw(screen)

        node = self.nodes.get(self.node_id, {})
        speaker = str(node.get("speaker", self.npc_id))
        text = str(node.get("text", ""))
        portrait_spec = node.get("portrait")

        tb_rect = pygame.Rect(0, SCREEN_H - UI_TEXTBOX_H, SCREEN_W, UI_TEXTBOX_H)
        self.textbox.draw(screen, tb_rect, text=text, speaker=speaker)

        if portrait_spec:
            portrait_rect = pygame.Rect(
                14,
                SCREEN_H - UI_TEXTBOX_H - PORTRAIT_BOX_H - 14,
                PORTRAIT_BOX_W,
                PORTRAIT_BOX_H,
            )
            pygame.draw.rect(screen, (28, 28, 40), portrait_rect)
            pygame.draw.rect(screen, (70, 70, 90), portrait_rect, 2)

            try:
                frames, fps = self._get_portrait_frames(portrait_spec)
                if frames:
                    surf = frames[0]
                    if fps > 0.0 and len(frames) > 1:
                        idx = int(self.portrait_anim_time * fps) % len(frames)
                        surf = frames[idx]

                    pad = PORTRAIT_BOX_PAD
                    inner = pygame.Rect(
                        portrait_rect.x + pad,
                        portrait_rect.y + pad,
                        portrait_rect.w - pad * 2,
                        portrait_rect.h - pad * 2,
                    )
                    pw, ph = surf.get_width(), surf.get_height()
                    scale = min(inner.w / max(1, pw), inner.h / max(1, ph))
                    sw = int(pw * scale)
                    sh = int(ph * scale)
                    img = pygame.transform.scale(surf, (sw, sh))
                    ix = inner.x + (inner.w - sw) // 2
                    iy = inner.y + (inner.h - sh) // 2
                    screen.blit(img, (ix, iy))
            except Exception:
                pass

        choices = node.get("choices")
        if isinstance(choices, list) and choices:
            labels: list[str] = []
            for c in choices:
                labels.append(str(c.get("label", "...")))

            cm_rect = pygame.Rect(SCREEN_W - 420, SCREEN_H - UI_TEXTBOX_H - 200, 400, 190)
            self.choice_menu.draw(screen, cm_rect, labels, self.selected_choice)

    def _get_portrait_frames(self, spec: object) -> tuple[list[pygame.Surface], float]:
        if isinstance(spec, str):
            path = spec
            surf = self.portrait_cache.get(path)
            if surf is None:
                surf = pygame.image.load(path).convert_alpha()
                self.portrait_cache[path] = surf
            return [surf], 0.0

        if isinstance(spec, dict):
            stype = str(spec.get("type", ""))
            if stype == "frames":
                fps = float(spec.get("fps", 8.0))
                frames_list = spec.get("frames", [])
                key = json.dumps({"type": "frames", "fps": fps, "frames": frames_list}, sort_keys=True)
                cached = self.portrait_anim_cache.get(key)
                if cached is not None:
                    return cached

                frames: list[pygame.Surface] = []
                if isinstance(frames_list, list):
                    for p in frames_list:
                        if not isinstance(p, str):
                            continue
                        frames.append(pygame.image.load(p).convert_alpha())

                if not frames:
                    return [], 0.0

                self.portrait_anim_cache[key] = (frames, fps)
                return frames, fps

        return [], 0.0


class ChallengeScene(BaseScene):
    def __init__(self, app: "App", return_scene: BaseScene, challenge_set_id: str):
        super().__init__(app)
        self.return_scene = return_scene
        self.challenge_set_id = challenge_set_id

        self.font = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 22)
        self.choice_menu = ChoiceMenu(self.small)

        self.data = self._load_challenge_set(challenge_set_id)
        self.title = str(self.data.get("title", challenge_set_id))
        self.category = str(self.data.get("category", "phishing"))
        self.questions = self.data.get("questions", [])

        self.qi = 0
        self.selected = 0
        self.showing_feedback = False
        self.last_correct = False
        self.last_expl = ""

        self.points_earned = 0
        self.max_points = 0
        for q in self.questions:
            self.max_points += int(q.get("points", 100))

    def _load_challenge_set(self, set_id: str) -> dict:
        path = os.path.join("data", "challenges", f"{set_id}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def handle_input(self, st: InputState, events: list[pygame.event.Event]) -> SceneResult:
        if st.cancel_pressed:
            save_game(self.app.save)
            return SceneResult(next_scene=self.return_scene)

        if not self.questions:
            return SceneResult(next_scene=ResultsScene(self.app, return_scene=self.return_scene, title=self.title, points=self.points_earned, max_points=self.max_points))

        q = self.questions[self.qi]
        choices = q.get("choices", [])

        if self.showing_feedback:
            if st.confirm_pressed:
                self.showing_feedback = False
                self.selected = 0
                self.qi += 1
                if self.qi >= len(self.questions):
                    comp = self.app.save.setdefault("completed", {}).setdefault("challenges", [])
                    if self.challenge_set_id not in comp:
                        comp.append(self.challenge_set_id)
                    save_game(self.app.save)
                    return SceneResult(next_scene=ResultsScene(self.app, return_scene=self.return_scene, title=self.title, points=self.points_earned, max_points=self.max_points))
            return SceneResult()

        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP:
                    self.selected -= 1
                elif ev.key == pygame.K_DOWN:
                    self.selected += 1

        if self.selected < 0:
            self.selected = 0
        if self.selected >= len(choices):
            self.selected = len(choices) - 1

        if st.confirm_pressed:
            correct_i = int(q.get("correct_index", 0))
            self.last_correct = (self.selected == correct_i)
            self.last_expl = str(q.get("explanation", ""))
            if self.last_correct:
                pts = int(q.get("points", 100))
                self.points_earned += pts
                scores = self.app.save.setdefault("scores", {})
                scores["total"] = int(scores.get("total", 0)) + pts
                scores[self.category] = int(scores.get(self.category, 0)) + pts
            self.showing_feedback = True
            save_game(self.app.save)

        return SceneResult()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((16, 14, 22))

        title = self.font.render(self.title, True, WHITE)
        screen.blit(title, (40, 30))

        if not self.questions:
            msg = self.font.render("No questions found.", True, RED)
            screen.blit(msg, (40, 120))
            return

        q = self.questions[self.qi]
        prompt = str(q.get("prompt", ""))
        choices = [str(c) for c in (q.get("choices", []) or [])]

        pygame.draw.rect(screen, (28, 28, 40), pygame.Rect(40, 90, SCREEN_W - 80, 170))
        pygame.draw.rect(screen, (70, 70, 90), pygame.Rect(40, 90, SCREEN_W - 80, 170), 2)

        x = 60
        y = 110
        max_w = SCREEN_W - 120
        words = prompt.split(" ")
        line = ""
        for w in words:
            test = w if line == "" else (line + " " + w)
            if self.small.size(test)[0] <= max_w:
                line = test
            else:
                screen.blit(self.small.render(line, True, WHITE), (x, y))
                y += 26
                line = w
        if line:
            screen.blit(self.small.render(line, True, WHITE), (x, y))

        if self.showing_feedback:
            color = GREEN if self.last_correct else RED
            msg = "Correct!" if self.last_correct else "Incorrect."
            screen.blit(self.font.render(msg, True, color), (40, 290))
            if self.last_expl:
                screen.blit(self.small.render(self.last_expl, True, WHITE), (40, 330))
            screen.blit(self.small.render("Press Enter to continue", True, (200, 200, 200)), (40, SCREEN_H - 40))
            return

        cm_rect = pygame.Rect(40, 300, SCREEN_W - 80, 330)
        self.choice_menu.draw(screen, cm_rect, choices, self.selected)

        hud = self.small.render(f"Question {self.qi + 1}/{len(self.questions)}   Points: {self.points_earned}/{self.max_points}", True, (200, 200, 200))
        screen.blit(hud, (40, SCREEN_H - 40))



class ResultsScene(BaseScene):
    def __init__(self, app: "App", return_scene: BaseScene, title: str, points: int, max_points: int):
        super().__init__(app)
        self.return_scene = return_scene
        self.title = title
        self.points = points
        self.max_points = max_points
        self.font = pygame.font.Font(None, 40)
        self.small = pygame.font.Font(None, 26)

    def _grade(self) -> str:
        if self.max_points <= 0:
            return "N/A"
        pct = (self.points * 100.0) / float(self.max_points)
        if pct >= 90.0:
            return "S"
        if pct >= 80.0:
            return "A"
        if pct >= 70.0:
            return "B"
        if pct >= 60.0:
            return "C"
        return "D"

    def handle_input(self, st: InputState, events: list[pygame.event.Event]) -> SceneResult:
        if st.confirm_pressed or st.cancel_pressed:
            return SceneResult(next_scene=self.return_scene)
        return SceneResult()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((12, 12, 18))
        screen.blit(self.font.render("Results", True, WHITE), (60, 60))
        screen.blit(self.small.render(self.title, True, (200, 200, 200)), (60, 110))

        grade = self._grade()
        screen.blit(self.font.render(f"Grade: {grade}", True, YELLOW), (60, 170))
        screen.blit(self.font.render(f"Points: {self.points}/{self.max_points}", True, WHITE), (60, 220))

        screen.blit(self.small.render("Press Enter to return", True, (200, 200, 200)), (60, SCREEN_H - 60))