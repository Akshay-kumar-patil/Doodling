import asyncio
import websockets
import json

async def hello():
    uri = "ws://localhost:8000/ws/room1/player1"
    async with websockets.connect(uri) as websocket:
        text = input("Enter message: ")
        
        # Send data to the server
        await websocket.send(json.dumps({
            "type": "chat",
            "data": {"text": text}
        }))
        print(f"> Sent: {text}")

        # Receive the response
        greeting = await websocket.recv()
        print(f"< Received: {greeting}")

if __name__ == "__main__":
    asyncio.run(hello())
