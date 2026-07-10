# Doodling

Doodling is a multiplayer drawing-and-guessing game built with FastAPI and a browser-based frontend. One player draws a hidden word while everyone else guesses in chat, and the game keeps score across rounds. The UI also includes an in-browser voice room powered by WebRTC signaling.

## Features

- Real-time drawing with WebSockets
- Room-based multiplayer gameplay
- Hidden word selection for the active drawer
- Guess chat, score tracking, and round rotation
- Optional voice chat room support
- A small standalone Tkinter drawing demo in `frontend/drawing.py`

## Project Layout

- `backend/server.py` - main game server
- `backend/combined_server.py` - mounts the game server and voice server together
- `backend/peer_voice_server.py` - voice signaling backend
- `backend/manager.py` - room, round, word, and scoring logic
- `frontend/` - HTML/CSS/JS client assets
- `run_combined_backend.py` - starts the combined app on port `8000`
- `run_peer_voice_backend.py` - starts the voice backend on port `8011`

## Requirements

- Python 3.10+
- `pip`

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Run The App

Start the combined backend:

```bash
python run_combined_backend.py
```

Then open:

```text
http://127.0.0.1:8000
```

### Voice Backend

The repo also includes a standalone voice signaling service:

```bash
python run_peer_voice_backend.py
```

This runs on:

```text
http://127.0.0.1:8011
```

The browser app uses the `/voice` path when it is served from the combined backend.

## How To Play

1. Open the app in a browser.
2. Create a room or connect to an existing room.
3. Wait for at least two players to join.
4. Start the round.
5. The drawer chooses one of the offered words and draws it.
6. Everyone else types guesses in the chat.
7. Scores update automatically, and the drawer rotates each round.

## Notes

- The game server serves the frontend from `frontend/index.html` and `/static/*`.
- If you want only the WebSocket/chat game, the combined backend is enough.
- The Tkinter drawing demo can be launched separately with:

```bash
python frontend/drawing.py
```

## Troubleshooting

- If the browser cannot connect, make sure `python run_combined_backend.py` is still running.
- If voice chat does not connect, check that microphone permissions are allowed in the browser.
- If you change the port or host, update the frontend URLs accordingly.
