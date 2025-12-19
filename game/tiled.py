from __future__ import annotations

import json
import os
from dataclasses import dataclass

import pygame


TILED_GID_MASK = 0x1FFFFFFF  # strips flip flags


def _props_list_to_dict(props: list[dict] | None) -> dict:
    out: dict = {}
    if not props:
        return out
    for p in props:
        out[str(p.get("name"))] = p.get("value")
    return out


@dataclass
class TiledObject:
    name: str
    x: float
    y: float
    w: float
    h: float
    properties: dict


class TiledMap:
    def __init__(self, json_path: str):
        self.json_path = json_path
        with open(json_path, "r", encoding="utf-8") as f:
            self.raw = json.load(f)

        self.width = int(self.raw.get("width", 0))
        self.height = int(self.raw.get("height", 0))
        self.tile_w = int(self.raw.get("tilewidth", 0))
        self.tile_h = int(self.raw.get("tileheight", 0))

        self.pixel_w = self.width * self.tile_w
        self.pixel_h = self.height * self.tile_h

        self.properties: dict = _props_list_to_dict(self.raw.get("properties"))

        self.tile_layers: list[dict] = []
        self.colliders: list[pygame.Rect] = []
        self.npcs: list[TiledObject] = []
        self.portals: list[TiledObject] = []
        self.books: list[TiledObject] = []

        self._tileset_firstgid = 1
        self._tileset_image: pygame.Surface | None = None
        self._tile_surfaces: list[pygame.Surface | None] = [None]  # gid 0 empty

        self._parse_layers()
        self._load_tileset()

    def _parse_layers(self) -> None:
        layers = self.raw.get("layers", [])
        for layer in layers:
            ltype = layer.get("type")
            if ltype == "tilelayer":
                self.tile_layers.append(layer)
            elif ltype == "objectgroup":
                lname = str(layer.get("name", "")).lower()
                if lname == "colliders":
                    for obj in layer.get("objects", []):
                        self.colliders.append(
                            pygame.Rect(
                                int(obj.get("x", 0)),
                                int(obj.get("y", 0)),
                                int(obj.get("width", 0)),
                                int(obj.get("height", 0)),
                            )
                        )
                elif lname == "npcs":
                    for obj in layer.get("objects", []):
                        props = _props_list_to_dict(obj.get("properties", []) or [])
                        self.npcs.append(
                            TiledObject(
                                name=str(obj.get("name", "npc")),
                                x=float(obj.get("x", 0.0)),
                                y=float(obj.get("y", 0.0)),
                                w=float(obj.get("width", 16.0)),
                                h=float(obj.get("height", 16.0)),
                                properties=props,
                            )
                        )
                elif lname == "portals":
                    # Rect objects that teleport player to another map/position.
                    # Properties (recommended):
                    # - target_map (string) e.g. house_1
                    # - target_x, target_y (number) spawn coords in pixels
                    # - target_zoom (number, optional)
                    # - prompt (string, optional) UI text
                    # - sprite (string, optional) path to sprite image
                    for obj in layer.get("objects", []):
                        props = _props_list_to_dict(obj.get("properties", []) or [])
                        self.portals.append(
                            TiledObject(
                                name=str(obj.get("name", "portal")),
                                x=float(obj.get("x", 0.0)),
                                y=float(obj.get("y", 0.0)),
                                w=float(obj.get("width", 16.0)),
                                h=float(obj.get("height", 16.0)),
                                properties=props,
                            )
                        )
                elif lname in ("books", "interactables"):
                    # Rect objects that open an info panel.
                    # Properties:
                    # - title (string)
                    # - text (string)
                    # - prompt (string, optional)
                    # - sprite (string, optional) path to sprite image
                    for obj in layer.get("objects", []):
                        props = _props_list_to_dict(obj.get("properties", []) or [])
                        self.books.append(
                            TiledObject(
                                name=str(obj.get("name", "book")),
                                x=float(obj.get("x", 0.0)),
                                y=float(obj.get("y", 0.0)),
                                w=float(obj.get("width", 16.0)),
                                h=float(obj.get("height", 16.0)),
                                properties=props,
                            )
                        )

    def _load_tileset(self) -> None:
        tilesets = self.raw.get("tilesets", [])
        if not tilesets:
            # No tileset: allow debug rendering
            return

        ts0 = tilesets[0]
        if "source" in ts0:
            raise RuntimeError(
                "This scaffold only supports embedded tilesets in Tiled JSON. "
                "In Tiled, try exporting with embedded tileset data."
            )

        self._tileset_firstgid = int(ts0.get("firstgid", 1))
        image_rel = ts0.get("image")
        if not image_rel:
            return

        # Resolve relative to the map file directory
        map_dir = os.path.dirname(self.json_path)
        image_path = os.path.normpath(os.path.join(map_dir, image_rel))
        self._tileset_image = pygame.image.load(image_path).convert_alpha()

        img_w = int(ts0.get("imagewidth", self._tileset_image.get_width()))
        img_h = int(ts0.get("imageheight", self._tileset_image.get_height()))
        tw = int(ts0.get("tilewidth", self.tile_w))
        th = int(ts0.get("tileheight", self.tile_h))
        cols = int(ts0.get("columns", max(1, img_w // tw)))
        tilecount = int(ts0.get("tilecount", (img_w // tw) * (img_h // th)))

        # Build a gid-indexed surface array (sparse)
        max_gid = self._tileset_firstgid + tilecount
        self._tile_surfaces = [None] * max_gid

        for i in range(tilecount):
            gid = self._tileset_firstgid + i
            sx = (i % cols) * tw
            sy = (i // cols) * th
            surf = pygame.Surface((tw, th), pygame.SRCALPHA)
            surf.blit(self._tileset_image, (0, 0), area=pygame.Rect(sx, sy, tw, th))
            self._tile_surfaces[gid] = surf

    def world_bounds_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.pixel_w, self.pixel_h)

    def get_npc_rects(self) -> list[pygame.Rect]:
        rects: list[pygame.Rect] = []
        for npc in self.npcs:
            rects.append(pygame.Rect(int(npc.x), int(npc.y), int(npc.w), int(npc.h)))
        return rects

    def draw(self, screen: pygame.Surface, camera_x: float, camera_y: float) -> None:
        # Visible tile range
        sw, sh = screen.get_size()
        if self.tile_w <= 0 or self.tile_h <= 0:
            return

        start_tx = int(camera_x // self.tile_w)
        start_ty = int(camera_y // self.tile_h)
        end_tx = int((camera_x + sw) // self.tile_w) + 1
        end_ty = int((camera_y + sh) // self.tile_h) + 1

        if start_tx < 0:
            start_tx = 0
        if start_ty < 0:
            start_ty = 0
        if end_tx > self.width:
            end_tx = self.width
        if end_ty > self.height:
            end_ty = self.height

        # Draw each tile layer in order
        for layer in self.tile_layers:
            data = layer.get("data")
            if not isinstance(data, list):
                continue

            lw = int(layer.get("width", self.width))
            lh = int(layer.get("height", self.height))
            if lw <= 0 or lh <= 0:
                continue

            for ty in range(start_ty, end_ty):
                row_i = ty * lw
                for tx in range(start_tx, end_tx):
                    gid_raw = int(data[row_i + tx])
                    gid = gid_raw & TILED_GID_MASK
                    if gid == 0:
                        continue

                    px = tx * self.tile_w - camera_x
                    py = ty * self.tile_h - camera_y

                    if 0 <= gid < len(self._tile_surfaces) and self._tile_surfaces[gid] is not None:
                        screen.blit(self._tile_surfaces[gid], (px, py))
                    else:
                        # Debug fallback tile
                        pygame.draw.rect(screen, (60, 80, 120), pygame.Rect(int(px), int(py), self.tile_w, self.tile_h))
