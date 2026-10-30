import requests
import json
import time
import websockets
import asyncio

BASE_URL = "http://localhost:7860"
WS_URL = "ws://localhost:7860/ws"

async def test_api():
    print("--- Auditando APIs ---")

    # 1. Status
    try:
        r = requests.get(f"{BASE_URL}/api/status")
        print(f"[API] /status: {r.status_code} - Model: {r.json().get('model_name')}")
    except:
        print("[API] /status: FALHA")

    # 2. Models
    try:
        r = requests.get(f"{BASE_URL}/api/models")
        models = r.json()
        print(f"[API] /models: {len(models)} modelos encontrados.")
    except:
        print("[API] /models: FALHA")

    # 3. History
    try:
        r = requests.get(f"{BASE_URL}/api/history")
        print(f"[API] /history: {len(r.json())} itens.")
    except:
        print("[API] /history: FALHA")

async def test_ws():
    print("\n--- Auditando WebSocket ---")
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("[WS] Conectado.")
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"[WS] Recebido: {data.get('type')}")
    except Exception as e:
        print(f"[WS] FALHA: {e}")

if __name__ == "__main__":
    # Nota: Requer que o servidor esteja rodando
    print("AVISO: Certifique-se de que main.py está rodando em uma janela separada.")
    asyncio.run(test_api())
    asyncio.run(test_ws())
