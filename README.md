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


The game loads maps from `data/maps/{map_id}.json`.
- By default it starts at `data/maps/city.json`.
- If a map file doesn’t exist yet, the game will fall back to a generated dev map.

