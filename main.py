import os
import asyncio
import json
import socket
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from runtime import runtime, Job
import qwen3_tts_backend

app = FastAPI(title="Qwen3-TTS Local Studio")

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "outputs"
MP3_DIR = BASE_DIR / "mp3out"

# Garantir diretórios
for d in [STATIC_DIR, OUTPUT_DIR, MP3_DIR]:
    d.mkdir(exist_ok=True)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()
main_loop: Optional[asyncio.AbstractEventLoop] = None

def on_runtime_event(event_type, data):
    # Serialização customizada para objetos complexos se necessário
    if hasattr(data, '__dict__'):
        data = data.__dict__

    global main_loop
    loop = main_loop
    if not loop or not loop.is_running():
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = None

    if loop and loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({"type": event_type, "data": data}),
                loop
            )
        except Exception as e:
            pass

runtime.add_listener(on_runtime_event)

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    asyncio.create_task(runtime.process_queue())

class GenerateRequest(BaseModel):
    model: str
    text: str
    language: str = "Portuguese"
    speaker: str = "Aiden"
    instruct: Optional[str] = None
    dtype: str = "float32"

class VoiceDesignRequest(BaseModel):
    model: str
    text: str
    instruct: str
    language: str = "Portuguese"
    dtype: str = "float32"

@app.get("/api/status")
async def get_status():
    return runtime.get_status()

@app.get("/api/diagnostics")
async def get_diagnostics():
    return runtime.get_diagnostics()

@app.get("/api/models")
async def list_models():
    return runtime.backend.list_models()

@app.get("/api/history")
async def get_history(limit: int = 20):
    return runtime.get_history(limit)

@app.post("/api/generate/custom")
async def generate_custom(req: GenerateRequest):
    job_id = await runtime.create_job("generate_custom", req.dict())
    return {"job_id": job_id}

@app.post("/api/generate/design")
async def generate_design(req: VoiceDesignRequest):
    job_id = await runtime.create_job("generate_design", req.dict())
    return {"job_id": job_id}

@app.post("/api/convert/mp3")
async def convert_mp3(wav_path: str):
    job_id = await runtime.create_job("convert_mp3", {"wav_path": wav_path})
    return {"job_id": job_id}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job = runtime.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return job

@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    success = await runtime.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível cancelar o job")
    return {"status": "ok"}

@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Procura em outputs ou mp3out
    paths = [OUTPUT_DIR / filename, MP3_DIR / filename]
    for p in paths:
        if p.exists():
            return FileResponse(p)

    raise HTTPException(status_code=404, detail="File not found")

@app.get("/api/lan-info")
async def get_lan_info():
    ip = get_ip()
    return {
        "local": "http://localhost:7860",
        "lan": f"http://{ip}:7860",
        "ip": ip
    }

@app.get("/api/qr")
async def get_qr():
    import qrcode
    from io import BytesIO
    from fastapi.responses import Response

    ip = get_ip()
    url = f"http://{ip}:7860"

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="white", back_color="#0a0a0a")
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Envia status inicial na conexão
        await websocket.send_json({"type": "INIT_STATUS", "data": runtime.get_status()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == "__main__":
    ip = get_ip()

    print("\n" + "=" * 48)
    print("          QWEN3STUDIO INICIADO")
    print("=" * 48)
    print("\nAcesso pelo computador:")
    print("http://localhost:7860")

    if ip != "127.0.0.1":
        print("\nAcesso pelo celular (mesma rede Wi-Fi):")
        print(f"http://{ip}:7860")
    else:
        print("\nNão foi possível detectar o IP da rede local.")

    print("\nPara conectar, mantenha o servidor aberto.")
    print("=" * 48 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="warning")