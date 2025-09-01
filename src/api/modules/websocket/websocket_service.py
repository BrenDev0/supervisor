from fastapi import WebSocket

class WebsocketService:
    def __init__(self):
        self.active_connections = {}

    def add_connection(self, connection_id:str, websocket: WebSocket):
        self.active_connections[connection_id] = websocket
        print(f"connection {connection_id} added.")
        return
    
    def get_connection(self, connection_id: str) -> WebSocket:
        connection = self.active_connections.get(connection_id)
        if not connection:
            print(f"Connection {connection_id} not found in get_connection()")

        return connection

    def remove_connection(self, connection_id: str):
        self.active_connections.pop(connection_id, None)
        print(f'Connection: {connection_id} was removed.')