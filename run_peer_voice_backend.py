import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "backend.peer_voice_server:app",
        host="0.0.0.0",
        port=8011,
        reload=True,
    )
