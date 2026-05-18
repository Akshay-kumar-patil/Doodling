from fastapi import FastAPI

try:
    from .server import app as game_app
    from .peer_voice_server import app as voice_app
except ImportError:
    from server import app as game_app
    from peer_voice_server import app as voice_app


app = FastAPI(title="Doodling Combined App")

# Mount voice first so /voice/* routes are handled there.
app.mount("/voice", voice_app)
app.mount("", game_app)
