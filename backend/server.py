import asyncio
import websockets

async def echo(websocket):
    # Listen for incoming messages
    async for message in websocket:
        print(f"Received from client: {message}")
        # Send a response back to the client
        await websocket.send(f"Server received: {message}")

async def main():
    # Start the server on localhost
    async with websockets.serve(echo, "localhost", 8765):
        print("Server started on ws://localhost:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())