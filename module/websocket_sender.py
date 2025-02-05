import asyncio
from fastapi import WebSocket, WebSocketDisconnect

# 웹소켓 메세지 
# 1. 콘솔출력
# 2. 웹소켓 send
# 3. 동기 blocking 해제

async def ws_send(ws : WebSocket, input : str):
    print(input)
    await ws.send_text(input)
    await asyncio.sleep(0)


# ping 자동 송신
async def ping_client(websocket: WebSocket):
    try:
        while True:
            await asyncio.sleep(30)  # 30초 대기
            print("ping 보냄")
            await websocket.send_json({"type": "ping"})
            
    except WebSocketDisconnect:
        print("클라이언트 연결 끊김")

    except asyncio.exceptions.CancelledError:
        pass  # 취소된 작업이므로 예외를 무시하고 처리