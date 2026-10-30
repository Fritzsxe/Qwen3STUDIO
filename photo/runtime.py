import asyncio
import uuid
import time
import threading
import torch
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from qwen3_tts_backend import Qwen3TTSBackend, MODELS, resolve_model

@dataclass
class Job:
    id: str
    type: str  # 'generate_custom', 'generate_design', 'generate_clone', 'convert_mp3'
    params: Dict[str, Any]
    status: str = "QUEUED"
    progress: float = 0.0
    message: str = "Aguardando na fila..."
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

class RuntimeManager:
    def __init__(self):
        self.backend = Qwen3TTSBackend()
        self.backend.add_listener(self._on_backend_event)
        self.jobs: Dict[str, Job] = {}
        self.active_job_id: Optional[str] = None
        self._queue = asyncio.Queue()
        self._stop_event = threading.Event()
        self.event_listeners: List[Callable] = []
        self.db_path = Path(__file__).parent / "history.db"

    def _on_backend_event(self, ev):
        self._notify("BACKEND_EVENT", {
            "status": ev.status,
            "message": ev.message,
            "progress": ev.progress,
            "model_key": ev.model_key,
            "model_name": ev.model_name,
            "request_id": ev.request_id,
            "details": getattr(ev, "details", {})
        })

    def add_listener(self, callback: Callable):
        self.event_listeners.append(callback)

    def _notify(self, event_type: str, data: Any):
        for listener in self.event_listeners:
            try:
                listener(event_type, data)
            except:
                pass

    async def create_job(self, job_type: str, params: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job = Job(id=job_id, type=job_type, params=params)
        self.jobs[job_id] = job
        await self._queue.put(job_id)
        self._notify("JOB_QUEUED", {"job_id": job_id, "type": job_type})
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    async def cancel_job(self, job_id: str):
        job = self.jobs.get(job_id)
        if not job: return False

        if job.status in ["QUEUED", "PROCESSING", "LOADING_MODEL", "GENERATING"]:
            job.status = "CANCELLED"
            job.message = "Cancelamento solicitado."
            if self.active_job_id == job_id:
                self.backend.request_cancel()
            self._notify("JOB_CANCELLED", {"job_id": job_id})
            return True
        return False

    async def process_queue(self):
        while not self._stop_event.is_set():
            job_id = await self._queue.get()
            job = self.jobs[job_id]
            self.active_job_id = job_id

            try:
                await self._run_job(job)
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                job.status = "FAILED"
                job.error = str(e)
                self._notify("JOB_FAILED", {"job_id": job_id, "error": str(e), "traceback": error_detail})
            finally:
                job.end_time = time.time()
                self._save_to_history(job)
                self.active_job_id = None
                self._queue.task_done()

    async def _run_job(self, job: Job):
        job.status = "PROCESSING"
        self._notify("JOB_STARTED", {"job_id": job.id, "type": job.type})

        loop = asyncio.get_running_loop()

        try:
            if job.type.startswith("generate"):
                model_name = job.params.get("model")
                dtype = job.params.get("dtype")

                if model_name:
                    job.status = "LOADING_MODEL"
                    job.message = f"Carregando {model_name}..."
                    self._notify("MODEL_LOAD_STARTED", {"job_id": job.id, "model": model_name})
                    await loop.run_in_executor(None, lambda: self.backend.load_model(model_name, dtype=dtype))
                    self._notify("MODEL_LOADED", {"job_id": job.id})

                job.status = "GENERATING"
                job.message = "Sintetizando áudio..."
                self._notify("GENERATION_STARTED", {"job_id": job.id})

                if job.type == "generate_custom":
                    out_filename = f"output_{job.id[:8]}.wav"
                    res = await loop.run_in_executor(None, lambda: self.backend.generate_custom_voice(
                        text=job.params["text"],
                        language=job.params.get("language", "Portuguese"),
                        speaker=job.params.get("speaker", "Aiden"),
                        instruct=job.params.get("instruct"),
                        output_path=out_filename
                    ))
                    try:
                        import shutil
                        src = Path(res["path"])
                        dst = Path(self.backend.output_dir) / "output_custom.wav"
                        if src.exists() and src != dst:
                            shutil.copy2(src, dst)
                    except:
                        pass
                    job.result = res

                elif job.type == "generate_design":
                    res = await loop.run_in_executor(None, lambda: self.backend.generate_voice_design(
                        text=job.params["text"],
                        instruct=job.params["instruct"],
                        language=job.params.get("language", "Portuguese")
                    ))
                    job.result = res

                elif job.type == "generate_clone":
                    res = await loop.run_in_executor(None, lambda: self.backend.generate_voice_clone(
                        text=job.params["text"],
                        ref_audio=job.params["ref_audio"],
                        ref_text=job.params["ref_text"],
                        language=job.params.get("language", "Portuguese"),
                        x_vector_only_mode=job.params.get("x_vector_only", False)
                    ))
                    job.result = res

                if job.status != "CANCELLED":
                    job.status = "COMPLETED"
                    self._notify("JOB_COMPLETED", {"job_id": job.id, "result": job.result})

            elif job.type == "convert_mp3":
                import audio_converter
                job.status = "CONVERTING"
                self._notify("CONVERSION_STARTED", {"job_id": job.id})
                success, path = await loop.run_in_executor(None, audio_converter.convert_wav_to_mp3, job.params["wav_path"])
                if success:
                    job.result = {"mp3_path": path}
                    job.status = "COMPLETED"
                    self._notify("CONVERSION_COMPLETED", {"job_id": job.id, "path": path})
                else:
                    raise RuntimeError(path)

        except Exception as e:
            raise e

    def _save_to_history(self, job: Job):
        if job.status != "COMPLETED": return
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT OR REPLACE INTO history (id, type, params, result, timestamp) VALUES (?, ?, ?, ?, ?)",
                (job.id, job.type, json.dumps(job.params), json.dumps(job.result), job.start_time)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao salvar histórico: {e}")

    def get_history(self, limit: int = 20):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except:
            return []

    def get_status(self):
        s = self.backend.status()
        active_job = self.jobs.get(self.active_job_id) if self.active_job_id else None
        s["active_job"] = active_job.__dict__ if active_job else None
        s["queue_size"] = self._queue.qsize()
        
        # Adiciona speakers e languages do modelo carregado (ou padrão oficial se não carregado)
        official_speakers = ['vivian', 'aiden', 'dylan', 'serena', 'ryan', 'eric', 'ono_anna', 'sohee', 'uncle_fu']
        official_languages = ['Portuguese', 'English', 'Chinese', 'Spanish', 'French', 'German', 'Italian', 'Japanese', 'Korean', 'Russian']

        if self.backend.model:
            try:
                s["supported_speakers"] = self.backend.get_speakers() or official_speakers
                s["supported_languages"] = self.backend.get_languages() or official_languages
            except:
                s["supported_speakers"] = official_speakers
                s["supported_languages"] = official_languages
        else:
            s["supported_speakers"] = official_speakers
            s["supported_languages"] = official_languages

        if not s.get("speakers"):
            s["speakers"] = s["supported_speakers"]
        if not s.get("languages"):
            s["languages"] = s["supported_languages"]

        return s

    def get_diagnostics(self):
        return self.backend.diagnostics()

runtime = RuntimeManager()
