from fastapi import WebSocket
from typing import Union
from uuid import UUID

class WebsocketService:
    def __init__(self):
        self.active_connections = {}

    def add_connection(self, connection_id: Union[UUID, str], websocket: WebSocket):
        key = str(connection_id)
        self.active_connections[key] = websocket
        print(f"connection {key} added.")
        return
    
    def get_connection(self, connection_id: Union[UUID, str]) -> WebSocket:
        key = str(connection_id)
        connection = self.active_connections.get(key)
        if not connection:
            print(f"Connection {key} not found in get_connection()")

        return connection

    def remove_connection(self, connection_id: str):
        key = str(connection_id)
        self.active_connections.pop(key, None)
        print(f'Connection: {key} was removed.')