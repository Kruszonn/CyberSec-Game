# Anime-Themed Security Training Game (Python + pygame)
This is a  scaffold for a top-down 2D security training game:


## Requirements
- Python 3.12+


```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Controls
- Move: `WASD`
- Interact: `E` (near NPC)
- Dialogue/menus: `Up/Down` + `Enter`
- Quit: `Esc`

## Content files
- Dialogues: `data/dialogues/*.json`
- Challenges: `data/challenges/*.json`
- Saves: `data/saves/slot1.json`

## Using Tiled (JSON export)
The game loads maps from `data/maps/{map_id}.json`.
- By default it starts at `data/maps/city.json`.
- If a map file doesn’t exist yet, the game will fall back to a generated dev map.


- Map tile size: 16x16
- Optional Map Property:
  - `default_zoom` (number, e.g. `1.0` for city, `1.6` for interiors)

### Collisions
Create an Object Layer named `Colliders` with rectangle objects for collisions.

### NPCs
Create an Object Layer named `NPCs` with rectangle objects.
Custom properties:
- `npc_id` (string, e.g. `aya`)
- `dialogue` (string path, e.g. `data/dialogues/npc_aya.json`)

### Portals (enter/exit buildings)
Create an Object Layer named `Portals` with rectangle objects.
Custom properties:
- `target_map` (string, e.g. `house_1`)
- `target_x` (number, spawn X in pixels)
- `target_y` (number, spawn Y in pixels)
- `target_zoom` (number, optional; overrides the target map’s `default_zoom`)
- `prompt` (string, optional; e.g. `Press E to exit`)

### Books / Interactables
Create an Object Layer named `Books` (or `Interactables`) with rectangle objects.
Custom properties:
- `title` (string)
- `text` (string)
- `prompt` (string, optional; shown at top-left)



## Dialogue portraits
In dialogue JSON (`data/dialogues/*.json`), `portrait` can be:
- A string path (static image):
  - PNG/JPG recommended
  - GIF will load as a static frame (pygame doesn’t animate GIFs by itself)
- A simple frame animation:
  - `{ "type": "frames", "fps": 8, "frames": ["a.png", "b.png"] }`

## Default sprite paths

- Player: `assets/sprites/player.png`
- NPCs: `assets/sprites/npc.png` (fallback)
  - Aya: `assets/sprites/npc_aya.png`
  - Mika: `assets/sprites/npc_mika.png`
  - Ren: `assets/sprites/npc_ren.png`
- Door/portal: `assets/sprites/door.png`
- Book: `assets/sprites/book.png`
- City background: `assets/tiles/city_bg.png`
- House sprites: `assets/tiles/house_a.png`, `assets/tiles/house_b.png`
- Interior background: `assets/tiles/house_1_bg.png`

## Next step
