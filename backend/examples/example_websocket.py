"""
Example: WebSocket Client for Smart City IoT Dashboard

This script demonstrates how to connect to the WebSocket endpoint
and receive real-time telemetry and alert updates.

Usage:
    python examples/example_websocket.py
"""

import asyncio
import json
import websockets
from datetime import datetime


async def websocket_client():
    """
    Connect to WebSocket endpoint and receive real-time updates.
    """
    uri = "ws://localhost:8000/ws"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Receive connection acknowledgment
            ack_message = await websocket.recv()
            ack_data = json.loads(ack_message)
            print(f"Received: {ack_data}")
            
            # Listen for messages
            message_count = 0
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=35)
                    data = json.loads(message)
                    
                    message_count += 1
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if data["type"] == "telemetry":
                        telemetry = data["data"]
                        print(f"\n[{timestamp}] Telemetry Update #{message_count}")
                        print(f"  Sensor ID: {telemetry.get('sensorId')}")
                        print(f"  Location ID: {telemetry.get('locationId')}")
                        print(f"  CO2: {telemetry.get('co2')} ppm")
                        print(f"  Noise: {telemetry.get('noise')} dB")
                        print(f"  Temperature: {telemetry.get('temperature')} °C")
                    
                    elif data["type"] == "alert":
                        alert = data["data"]
                        print(f"\n[{timestamp}] ⚠️  ALERT #{message_count}")
                        print(f"  Alert ID: {alert.get('alertId')}")
                        print(f"  Sensor ID: {alert.get('sensorId')}")
                        print(f"  Metric: {alert.get('metricType')}")
                        print(f"  Value: {alert.get('value')}")
                        print(f"  Level: {alert.get('level')}")
                    
                    elif data["type"] == "heartbeat":
                        print(f"[{timestamp}] ❤️  Heartbeat received")
                    
                    else:
                        print(f"[{timestamp}] Unknown message type: {data['type']}")
                
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send(json.dumps({"type": "ping"}))
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sent ping")
    
    except websockets.exceptions.ConnectionClosed:
        print("\nConnection closed by server")
    except KeyboardInterrupt:
        print("\nDisconnected by user")
    except Exception as e:
        print(f"\nError: {e}")


async def websocket_client_with_ping():
    """
    Connect to WebSocket endpoint and send periodic pings.
    """
    uri = "ws://localhost:8000/ws"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Receive connection acknowledgment
            ack_message = await websocket.recv()
            ack_data = json.loads(ack_message)
            print(f"Received: {ack_data}")
            
            # Create tasks for sending pings and receiving messages
            async def send_pings():
                while True:
                    await asyncio.sleep(20)
                    await websocket.send(json.dumps({"type": "ping"}))
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sent ping")
            
            async def receive_messages():
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if data["type"] == "pong":
                        print(f"[{timestamp}] Received pong")
                    elif data["type"] == "heartbeat":
                        print(f"[{timestamp}] ❤️  Heartbeat received")
                    elif data["type"] == "telemetry":
                        telemetry = data["data"]
                        print(f"[{timestamp}] Telemetry: Sensor {telemetry.get('sensorId')}, "
                              f"CO2={telemetry.get('co2')} ppm")
                    elif data["type"] == "alert":
                        alert = data["data"]
                        print(f"[{timestamp}] ⚠️  Alert: {alert.get('metricType')} = "
                              f"{alert.get('value')} ({alert.get('level')})")
            
            # Run both tasks concurrently
            await asyncio.gather(send_pings(), receive_messages())
    
    except websockets.exceptions.ConnectionClosed:
        print("\nConnection closed by server")
    except KeyboardInterrupt:
        print("\nDisconnected by user")
    except Exception as e:
        print(f"\nError: {e}")


def main():
    """
    Main function to run WebSocket client examples.
    """
    print("=" * 60)
    print("WebSocket Client Example")
    print("=" * 60)
    print("\nThis example connects to the WebSocket endpoint and")
    print("receives real-time telemetry and alert updates.")
    print("\nPress Ctrl+C to disconnect\n")
    
    # Choose which example to run
    print("Select example:")
    print("1. Basic client (receive messages)")
    print("2. Client with ping/pong")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        asyncio.run(websocket_client_with_ping())
    else:
        asyncio.run(websocket_client())


if __name__ == "__main__":
    main()
