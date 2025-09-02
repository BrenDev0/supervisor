from fastapi import APIRouter, WebSocket, status, WebSocketDisconnect
from uuid import UUID
from src.api.modules.websocket.ws_hmac_verification import verify_hmac_ws
from src.dependencies.container import Container
from src.api.modules.websocket.websocket_service import WebsocketService


router = APIRouter()


@router.websocket("/ws/secure/interact/{chat_id}")
async def websocket_interact(websocket: WebSocket, chat_id: UUID):
    await websocket.accept()
    params = websocket.query_params
    signature = params.get("x-signature")
    payload = params.get("x-payload")

    if not await verify_hmac_ws(signature, payload):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    websocket_service: WebsocketService = Container.resolve("websocket_service")
    websocket_service.add_connection(chat_id, websocket)
    
    print(f'Websocket connection: {chat_id} opened.')
    try:
        while True: 
            await websocket.receive_text()

    except WebSocketDisconnect:
        websocket_service.remove_connection(chat_id)
        print(f'Websocket connection: {chat_id} closed.')