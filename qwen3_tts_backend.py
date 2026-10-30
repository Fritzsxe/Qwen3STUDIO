
# ================================================================
# QWEN3-TTS BACKEND ENGINE
# ================================================================
#
# Backend modular, pensado desde o início para uma futura UI.
#
# Objetivos:
#   - 5 modelos oficiais da família Qwen3-TTS
#   - comandos case-insensitive
#   - aliases para seleção
#   - download e cache local
#   - somente UM modelo carregado por vez
#   - descarregamento + limpeza de VRAM antes da troca
#   - geração CustomVoice / VoiceDesign / VoiceClone
#   - entrada de áudio como caminho, bytes ou objeto de arquivo
#   - sistema de eventos para uma futura UI
#   - mensagens de estado:
#       ANALISANDO
#       PENSANDO
#       CARREGANDO
#       GERANDO
#       PRONTO
#       ERRO
#   - API Python limpa para a futura UI
#   - CLI completamente funcional agora
#
# Observação importante:
# "Pensando" aqui é um ESTADO DA INTERFACE, não uma exposição
# de cadeia de pensamento interna do modelo. É apenas feedback
# visual de que o backend está processando a solicitação.
#
# ================================================================

from __future__ import annotations

import copy
import gc
import io
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import audio_converter


# ================================================================
# CONFIGURAÇÃO
# ================================================================

APP_NAME = "Qwen3-TTS Backend"
VERSION = "0.2.0"

MODEL_DIRECTORY = Path("./models")
OUTPUT_DIRECTORY = Path("./outputs")

MODEL_DIRECTORY.mkdir(parents=True, exist_ok=True)
OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

DEFAULT_DEVICE = "cuda:0"
DEFAULT_DTYPE = "float32"
DEFAULT_ATTENTION = "sdpa"


# ================================================================
# MODELOS
# ================================================================

MODELS: dict[str, dict[str, Any]] = {
    "1.7b-customvoice": {
        "id": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        "name": "1.7B CustomVoice",
        "family": "1.7B",
        "type": "customvoice",
        "description": "Vozes oficiais + instruction control.",
        "supports_instruct": True,
        "supports_speaker": True,
        "supports_clone": False,
        "supports_voice_design": False,
    },
    "1.7b-voicedesign": {
        "id": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        "name": "1.7B VoiceDesign",
        "family": "1.7B",
        "type": "voicedesign",
        "description": "Criação de voz a partir de descrição textual.",
        "supports_instruct": True,
        "supports_speaker": False,
        "supports_clone": False,
        "supports_voice_design": True,
    },
    "1.7b-base": {
        "id": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        "name": "1.7B Base",
        "family": "1.7B",
        "type": "base",
        "description": "Voice cloning.",
        "supports_instruct": False,
        "supports_speaker": False,
        "supports_clone": True,
        "supports_voice_design": False,
    },
    "0.6b-customvoice": {
        "id": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        "name": "0.6B CustomVoice",
        "family": "0.6B",
        "type": "customvoice",
        "description": "Vozes oficiais, versão compacta.",
        "supports_instruct": False,
        "supports_speaker": True,
        "supports_clone": False,
        "supports_voice_design": False,
    },
    "0.6b-base": {
        "id": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        "name": "0.6B Base",
        "family": "0.6B",
        "type": "base",
        "description": "Voice cloning, versão compacta.",
        "supports_instruct": False,
        "supports_speaker": False,
        "supports_clone": True,
        "supports_voice_design": False,
    },
}


# ================================================================
# ALIASES
# ================================================================
#
# Tudo passa por normalize().
#
# Qwen
# QWEN
# qWeN
#
# viram a mesma coisa.
# ================================================================

ALIASES: dict[str, str] = {
    # 1.7B CustomVoice
    "1.7b-customvoice": "1.7b-customvoice",
    "1.7b customvoice": "1.7b-customvoice",
    "1.7b custom voice": "1.7b-customvoice",
    "17b-customvoice": "1.7b-customvoice",
    "17b customvoice": "1.7b-customvoice",
    "customvoice 1.7b": "1.7b-customvoice",
    "custom 1.7b": "1.7b-customvoice",
    "customvoice": "1.7b-customvoice",

    # 1.7B VoiceDesign
    "1.7b-voicedesign": "1.7b-voicedesign",
    "1.7b voicedesign": "1.7b-voicedesign",
    "1.7b voice design": "1.7b-voicedesign",
    "17b-voicedesign": "1.7b-voicedesign",
    "voice design": "1.7b-voicedesign",
    "voicedesign": "1.7b-voicedesign",
    "design": "1.7b-voicedesign",

    # 1.7B Base
    "1.7b-base": "1.7b-base",
    "1.7b base": "1.7b-base",
    "17b-base": "1.7b-base",
    "base 1.7b": "1.7b-base",
    "clone 1.7b": "1.7b-base",
    "clone1.7b": "1.7b-base",

    # 0.6B CustomVoice
    "0.6b": "0.6b-customvoice",
    "0.6b-customvoice": "0.6b-customvoice",
    "0.6b customvoice": "0.6b-customvoice",
    "0.6b custom voice": "0.6b-customvoice",
    "06b-customvoice": "0.6b-customvoice",
    "customvoice 0.6b": "0.6b-customvoice",
    "custom 0.6b": "0.6b-customvoice",
    "custom 0.6": "0.6b-customvoice",

    # 1.7B CustomVoice alias
    "1.7b": "1.7b-customvoice",

    # 0.6B Base
    "0.6b-base": "0.6b-base",
    "0.6b base": "0.6b-base",
    "06b-base": "0.6b-base",
    "base 0.6b": "0.6b-base",
    "clone 0.6b": "0.6b-base",
    "clone0.6b": "0.6b-base",
}


# ================================================================
# ESTADOS DE EVENTO
# ================================================================

STATUS_IDLE = "idle"
STATUS_ANALYZING = "analyzing"
STATUS_THINKING = "thinking"
STATUS_LOADING = "loading"
STATUS_GENERATING = "generating"
STATUS_READY = "ready"
STATUS_ERROR = "error"
STATUS_UNLOADING = "unloading"
STATUS_DOWNLOADING = "downloading"
STATUS_CANCELED = "canceled"


@dataclass(slots=True)
class BackendEvent:
    """
    Evento emitido pelo backend.

    Uma futura UI pode simplesmente assinar on_event()
    e transformar isso em:
        "Estou analisando..."
        "Carregando..."
        "Gerando..."
        etc.
    """

    status: str
    message: str
    progress: Optional[float] = None
    model_key: Optional[str] = None
    model_name: Optional[str] = None
    request_id: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


EventListener = Callable[[BackendEvent], None]


# ================================================================
# NORMALIZAÇÃO
# ================================================================

def normalize(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = " ".join(text.split())
    return text


def resolve_model(value: Any) -> Optional[str]:
    """
    Resolve uma entrada humana para a chave interna.
    """
    key = normalize(value)

    if key in MODELS:
        return key

    return ALIASES.get(key)


# ================================================================
# PATCH DE COMPATIBILIDADE
# ================================================================

def apply_runtime_patches() -> None:
    """
    Workaround para o erro observado no ambiente:
        cannot pickle 'dict_keys' object

    Aplicado uma vez no startup.
    """
    try:
        key_type = type({}.keys())
        copy._deepcopy_dispatch[key_type] = lambda x, memo: list(x)
    except Exception:
        # Não derruba o backend só por causa do patch.
        pass


# ================================================================
# UTILITÁRIOS DE DEPENDÊNCIAS
# ================================================================

def import_runtime():
    try:
        import torch
        import soundfile as sf
    except ImportError as exc:
        raise RuntimeError(
            "Dependência ausente.\n"
            "Instale pelo menos:\n"
            "  pip install -U torch soundfile"
        ) from exc

    return torch, sf


def import_qwen():
    try:
        from qwen_tts import Qwen3TTSModel
    except ImportError as exc:
        raise RuntimeError(
            "qwen-tts não está instalado.\n"
            "Instale com:\n"
            "  pip install -U qwen-tts"
        ) from exc

    return Qwen3TTSModel


# ================================================================
# GPU
# ================================================================

def cuda_available() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def gpu_info() -> dict[str, Any]:
    try:
        import torch
    except ImportError:
        return {
            "available": False,
            "error": "torch não instalado",
        }

    if not torch.cuda.is_available():
        return {
            "available": False,
            "name": None,
            "total_gb": 0.0,
            "allocated_gb": 0.0,
            "reserved_gb": 0.0,
            "free_gb": 0.0,
        }

    device_index = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(device_index)

    total = int(props.total_memory)
    allocated = int(torch.cuda.memory_allocated(device_index))
    reserved = int(torch.cuda.memory_reserved(device_index))
    free = max(total - reserved, 0)

    return {
        "available": True,
        "index": device_index,
        "name": torch.cuda.get_device_name(device_index),
        "total_gb": total / 1024**3,
        "allocated_gb": allocated / 1024**3,
        "reserved_gb": reserved / 1024**3,
        "free_gb": free / 1024**3,
    }


def print_gpu_info(label: str = "GPU") -> None:
    info = gpu_info()

    print()
    print(f"--- {label} ---")

    if not info.get("available"):
        print("CUDA indisponível.")
        return

    print(f"GPU:        {info['name']}")
    print(f"VRAM total: {info['total_gb']:.2f} GB")
    print(f"Alocada:    {info['allocated_gb']:.2f} GB")
    print(f"Reservada:  {info['reserved_gb']:.2f} GB")
    print(f"Livre*:     {info['free_gb']:.2f} GB")
    print("* livre dentro do contexto de memória reservada pelo processo")


# ================================================================
# CLEANUP
# ================================================================

def cleanup_memory() -> None:
    gc.collect()

    try:
        import torch
    except ImportError:
        return

    if not torch.cuda.is_available():
        return

    for action in (
        torch.cuda.synchronize,
        torch.cuda.empty_cache,
        torch.cuda.ipc_collect,
    ):
        try:
            action()
        except Exception:
            pass

    gc.collect()


# ================================================================
# CAMINHOS / DOWNLOAD
# ================================================================

def get_hf_cache_dir() -> Path:
    """
    Descobre o diretório de cache do Hugging Face de forma robusta.
    """
    try:
        from huggingface_hub.constants import HF_HUB_CACHE
        return Path(HF_HUB_CACHE)
    except (ImportError, AttributeError):
        # Fallback manual se o SDK falhar ou for versão antiga.
        return Path.home() / ".cache" / "huggingface" / "hub"


def _is_snapshot_complete(path: Path) -> bool:
    """
    Verifica se um diretório contém os arquivos essenciais para ser
    considerado um modelo Qwen3-TTS utilizável.
    """
    if not path.is_dir():
        return False

    # 1. Configuração básica
    if not (path / "config.json").exists():
        return False

    # 2. Pesos (Safetensors único, shardado ou index)
    has_weights = (
        (path / "model.safetensors").exists() or
        (path / "model.safetensors.index.json").exists() or
        len(list(path.glob("model-*.safetensors"))) > 0 or
        (path / "pytorch_model.bin").exists()
    )
    if not has_weights:
        return False

    # 3. Tokenizer (Pode estar na raiz ou na subpasta speech_tokenizer)
    has_tokenizer = (
        (path / "tokenizer_config.json").exists() or
        (path / "speech_tokenizer" / "config.json").exists()
    )
    if not has_tokenizer:
        return False

    return True


def find_hf_snapshot(repo_id: str) -> Optional[Path]:
    cache_dir = get_hf_cache_dir()
    repo_folder_name = f"models--{repo_id.replace('/', '--')}"
    repo_path = cache_dir / repo_folder_name

    if not repo_path.exists():
        return None

    # 1. Prioridade: snapshot apontado por refs/main (o mais atual/oficial)
    ref_main_path = repo_path / "refs" / "main"
    if ref_main_path.exists():
        try:
            commit_hash = ref_main_path.read_text().strip()
            snapshot_path = repo_path / "snapshots" / commit_hash
            if _is_snapshot_complete(snapshot_path):
                return snapshot_path
        except (OSError, ValueError):
            pass

    # 2. Fallback: procurar qualquer snapshot completo
    snapshots_dir = repo_path / "snapshots"
    if snapshots_dir.exists():
        try:
            # Ordena por data de modificação para tentar pegar o mais recente
            snapshots = sorted(
                [d for d in snapshots_dir.iterdir() if d.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            for snapshot in snapshots:
                if _is_snapshot_complete(snapshot):
                    return snapshot
        except OSError:
            pass

    return None


def local_model_path(model_key: str) -> Path:
    model = MODELS[model_key]
    folder = model["id"].split("/")[-1]
    return MODEL_DIRECTORY / folder


def is_model_downloaded(model_key: str) -> bool:
    """
    Verifica se o modelo está disponível localmente (./models ou HF Cache).
    """
    # 1. Verifica ./models
    path = local_model_path(model_key)
    if _is_snapshot_complete(path):
        return True

    # 2. Verifica HF Cache
    repo_id = MODELS[model_key]["id"]
    if find_hf_snapshot(repo_id) is not None:
        return True

    return False


def model_source(model_key: str) -> str:
    # Prioridade 1: ./models (Cache explícito do backend)
    path = local_model_path(model_key)
    if _is_snapshot_complete(path):
        return str(path)

    # Prioridade 2: Hugging Face Cache (Transparente)
    repo_id = MODELS[model_key]["id"]
    hf_path = find_hf_snapshot(repo_id)
    if hf_path is not None:
        return str(hf_path)

    # Prioridade 3: Nuvem
    return repo_id


def get_model_origin(model_key: str) -> str:
    """
    Informa textualmente de onde o modelo virá.
    """
    path = local_model_path(model_key)
    if _is_snapshot_complete(path):
        return "Local (./models)"

    repo_id = MODELS[model_key]["id"]
    if find_hf_snapshot(repo_id) is not None:
        return "Hugging Face Cache"

    return "Nuvem (Download necessário)"


# ================================================================
# BACKEND ENGINE
# ================================================================

class Qwen3TTSBackend:
    """
    Motor principal.

    Conceito:
        UI -> Backend -> Qwen3TTSModel

    A UI não precisa conhecer o modelo internamente.
    Ela só precisa chamar os métodos públicos.
    """

    def __init__(
        self,
        *,
        device: str = DEFAULT_DEVICE,
        dtype: str = DEFAULT_DTYPE,
        attention: str = DEFAULT_ATTENTION,
        model_dir: str | Path = MODEL_DIRECTORY,
        output_dir: str | Path = OUTPUT_DIRECTORY,
    ):
        apply_runtime_patches()

        self.device = device
        self.dtype_name = normalize(dtype)
        self.attention = normalize(attention)

        self.model_dir = Path(model_dir)
        self.output_dir = Path(output_dir)

        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model: Any = None
        self.model_key: Optional[str] = None
        self.model_id: Optional[str] = None
        self.model_type: Optional[str] = None
        self.loaded_at: Optional[float] = None

        self.last_generation: Optional[dict[str, Any]] = None

        self._listeners: list[EventListener] = []
        self._cancel_requested = False

    # ============================================================
    # EVENTOS
    # ============================================================

    def add_listener(self, listener: EventListener) -> None:
        """
        Registra um callback.

        Exemplo futuro de UI:
            backend.add_listener(ui.handle_backend_event)
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: EventListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def emit(
        self,
        status: str,
        message: str,
        *,
        progress: Optional[float] = None,
        request_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> BackendEvent:
        event = BackendEvent(
            status=status,
            message=message,
            progress=progress,
            model_key=self.model_key,
            model_name=(
                MODELS[self.model_key]["name"]
                if self.model_key in MODELS
                else None
            ),
            request_id=request_id,
            details=details or {},
        )

        # CLI recebe uma cópia visual dos eventos.
        print(f"[{status.upper()}] {message}")

        # UI recebe o evento estruturado.
        for listener in tuple(self._listeners):
            try:
                listener(event)
            except Exception as exc:
                # Um bug na UI não deve derrubar o TTS.
                print(
                    f"[EVENT] Listener ignorado por erro: {exc}"
                )

        return event

    # ============================================================
    # CANCELAMENTO
    # ============================================================

    def request_cancel(self) -> None:
        """
        Marca o request atual como cancelado.

        O backend consegue interromper entre etapas.
        Uma chamada interna do model.generate() pode não ser
        interrompível imediatamente dependendo do backend.
        """
        self._cancel_requested = True

    def clear_cancel(self) -> None:
        self._cancel_requested = False

    def _check_cancel(self) -> None:
        if self._cancel_requested:
            self.emit(
                STATUS_CANCELED,
                "Operação cancelada.",
            )
            self._cancel_requested = False
            raise RuntimeError("Operação cancelada pelo usuário.")

    # ============================================================
    # LISTAGEM
    # ============================================================

    def list_models(self) -> list[dict[str, Any]]:
        result = []

        for key, data in MODELS.items():
            result.append(
                {
                    "key": key,
                    "name": data["name"],
                    "id": data["id"],
                    "type": data["type"],
                    "family": data["family"],
                    "description": data["description"],
                    "downloaded": is_model_downloaded(key),
                    "origin": get_model_origin(key),
                    "loaded": self.model_key == key,
                }
            )

        return result

    def print_models(self) -> None:
        print()
        print("=" * 82)
        print("MODELOS QWEN3-TTS")
        print("=" * 82)

        for index, item in enumerate(
            self.list_models(),
            start=1,
        ):
            marker = "  <-- CARREGADO" if item["loaded"] else ""
            downloaded = "SIM" if item["downloaded"] else "NÃO"

            print()
            print(f"[{index}] {item['name']}{marker}")
            print(f"    chave:     {item['key']}")
            print(f"    HF:        {item['id']}")
            print(f"    tipo:      {item['type']}")
            print(f"    baixado:   {downloaded}")
            print(f"    origem:    {item['origin']}")
            print(f"    descrição: {item['description']}")

        print()
        print("=" * 82)

    # ============================================================
    # DOWNLOAD
    # ============================================================

    def download_model(
        self,
        model_name: str,
        *,
        force: bool = False,
    ) -> Path:
        model_key = resolve_model(model_name)

        if model_key is None:
            raise ValueError(
                f"Modelo não reconhecido: {model_name}"
            )

        info = MODELS[model_key]
        repo_id = info["id"]

        # Se já está baixado (em ./models ou HF Cache), não duplica.
        if is_model_downloaded(model_key) and not force:
            source = model_source(model_key)
            self.emit(
                STATUS_READY,
                f"{info['name']} já está disponível localmente ({get_model_origin(model_key)}).",
                progress=1.0,
            )
            return Path(source)

        try:
            from huggingface_hub import snapshot_download
        except ImportError as exc:
            raise RuntimeError(
                "huggingface_hub não está instalado."
            ) from exc

        self.emit(
            STATUS_DOWNLOADING,
            f"Baixando {info['name']} para o cache do Hugging Face...",
            progress=0.0,
            details={
                "model_key": model_key,
                "repo_id": repo_id,
            },
        )

        # O download padrão vai para o HF Cache do usuário.
        # Isso evita duplicar 2GB+ na pasta do projeto se já existir no Hub.
        path_str = snapshot_download(repo_id=repo_id)
        destination = Path(path_str)

        self.emit(
            STATUS_READY,
            f"Download de {info['name']} concluído.",
            progress=1.0,
            details={"path": str(destination)},
        )

        return destination

    # ============================================================
    # DTYPE
    # ============================================================

    @staticmethod
    def resolve_dtype(dtype_name: str):
        import torch

        name = normalize(dtype_name)

        table = {
            "fp32": torch.float32,
            "float32": torch.float32,
            "32": torch.float32,

            "fp16": torch.float16,
            "float16": torch.float16,
            "16": torch.float16,

            "bf16": torch.bfloat16,
            "bfloat16": torch.bfloat16,
        }

        if name not in table:
            raise ValueError(
                "dtype inválido. Use fp32, fp16 ou bf16."
            )

        return table[name]

    # ============================================================
    # CARREGAMENTO
    # ============================================================

    def load_model(
        self,
        model_name: str,
        *,
        dtype: Optional[str] = None,
        device: Optional[str] = None,
        attention: Optional[str] = None,
        use_local: bool = True,
    ) -> Any:
        model_key = resolve_model(model_name)

        if model_key is None:
            raise ValueError(
                f"Modelo não reconhecido: {model_name}"
            )

        # Se já for o mesmo modelo, não recarrega à toa.
        if self.model is not None and self.model_key == model_key:
            self.emit(
                STATUS_READY,
                f"{MODELS[model_key]['name']} já está carregado.",
                progress=1.0,
            )
            return self.model

        # Troca de modelo = descarrega primeiro.
        if self.model is not None:
            self.unload_model()

        self._check_cancel()

        dtype_name = normalize(dtype or self.dtype_name)
        device_name = device or self.device
        attention_name = normalize(
            attention if attention is not None else self.attention
        )

        self.dtype_name = dtype_name
        self.device = device_name
        self.attention = attention_name

        info = MODELS[model_key]
        source = (
            model_source(model_key)
            if use_local
            else info["id"]
        )

        self.emit(
            STATUS_LOADING,
            f"Vou carregar {info['name']}.",
            progress=0.0,
            details={
                "source": source,
                "type": info["type"],
            },
        )

        self.emit(
            STATUS_THINKING,
            f"Preparando o carregamento de {info['name']}...",
            progress=0.05,
        )

        torch, _ = import_runtime()

        if device_name.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA foi solicitado, mas não está disponível."
            )

        Qwen3TTSModel = import_qwen()

        torch_dtype = self.resolve_dtype(dtype_name)

        kwargs: dict[str, Any] = {
            "device_map": device_name,
            "dtype": torch_dtype,
            "trust_remote_code": True,
        }

        if attention_name:
            kwargs["attn_implementation"] = attention_name

        print()
        print("=" * 82)
        print(f"CARREGANDO: {info['name']}")
        print("=" * 82)
        print(f"Fonte:     {source}")
        print(f"Tipo:      {info['type']}")
        print(f"Device:    {device_name}")
        print(f"Dtype:     {dtype_name}")
        print(f"Attention: {attention_name}")

        print_gpu_info("Antes do carregamento")

        start = time.perf_counter()

        try:
            self.model = Qwen3TTSModel.from_pretrained(
                source,
                **kwargs,
            )
        except Exception as exc:
            self.model = None

            self.emit(
                STATUS_ERROR,
                f"Falha ao carregar {info['name']}.",
                details={
                    "exception": repr(exc),
                    "traceback": traceback.format_exc(),
                },
            )
            raise

        elapsed = time.perf_counter() - start

        self.model_key = model_key
        self.model_id = info["id"]
        self.model_type = info["type"]
        self.loaded_at = time.time()

        # Correção do bug do wrapper para liberar o parâmetro 'instruct' no modelo 0.6B
        if hasattr(self.model, 'model') and hasattr(self.model.model, 'tts_model_size'):
            self.model.model.tts_model_size = "fixed"

        try:
            supported_languages = self.model.get_supported_languages()
        except Exception:
            supported_languages = []

        try:
            supported_speakers = self.model.get_supported_speakers()
        except Exception:
            supported_speakers = []

        print()
        print(f"Modelo carregado em {elapsed:.2f}s")
        print(f"Idiomas:  {supported_languages}")
        print(f"Speakers: {supported_speakers}")
        print_gpu_info("Depois do carregamento")

        self.emit(
            STATUS_READY,
            f"{info['name']} carregado e pronto.",
            progress=1.0,
            details={
                "load_time": elapsed,
                "languages": supported_languages,
                "speakers": supported_speakers,
            },
        )

        return self.model

    # ============================================================
    # DESCARREGAR
    # ============================================================

    def unload_model(self) -> bool:
        if self.model is None:
            cleanup_memory()
            return True

        old_key = self.model_key
        old_name = (
            MODELS[old_key]["name"]
            if old_key in MODELS
            else str(old_key)
        )

        self.emit(
            STATUS_UNLOADING,
            f"Descarregando {old_name}...",
            progress=0.0,
        )

        try:
            # Solta a referência do objeto.
            self.model = None

            # Solta estado associado.
            self.model_key = None
            self.model_id = None
            self.model_type = None
            self.loaded_at = None

            self.last_generation = None

            cleanup_memory()

        except Exception as exc:
            self.emit(
                STATUS_ERROR,
                f"Erro ao descarregar {old_name}.",
                details={"exception": repr(exc)},
            )
            raise

        self.emit(
            STATUS_READY,
            "Modelo descarregado. VRAM liberada na medida possível.",
            progress=1.0,
        )

        print_gpu_info("Após descarregamento")
        return True

    # ============================================================
    # STATUS
    # ============================================================

    def status(self) -> dict[str, Any]:
        current = None

        if self.model_key in MODELS:
            current = MODELS[self.model_key]

        return {
            "version": VERSION,
            "loaded": self.model is not None,
            "model_key": self.model_key,
            "model_id": self.model_id,
            "model_type": self.model_type,
            "model_name": current["name"] if current else None,
            "device": self.device,
            "dtype": self.dtype_name,
            "attention": self.attention,
            "gpu": gpu_info(),
            "last_generation": self.last_generation,
        }

    def print_status(self) -> None:
        data = self.status()

        print()
        print("=" * 82)
        print("STATUS DO BACKEND")
        print("=" * 82)

        print(f"Versão:    {data['version']}")
        print(f"Carregado: {data['loaded']}")
        print(f"Modelo:    {data['model_name']}")
        print(f"Tipo:      {data['model_type']}")
        print(f"Device:    {data['device']}")
        print(f"Dtype:     {data['dtype']}")
        print(f"Attention: {data['attention']}")

        if data["last_generation"]:
            print()
            print("Última geração:")
            for key, value in data["last_generation"].items():
                print(f"  {key}: {value}")

        print_gpu_info("GPU")
        print("=" * 82)

    # ============================================================
    # INFORMAÇÕES DO MODELO
    # ============================================================

    def get_languages(self) -> list[str]:
        if self.model is None:
            raise RuntimeError("Nenhum modelo carregado.")

        try:
            return list(self.model.get_supported_languages())
        except Exception:
            return []

    def get_speakers(self) -> list[str]:
        if self.model is None:
            raise RuntimeError("Nenhum modelo carregado.")

        try:
            return list(self.model.get_supported_speakers())
        except Exception:
            return []

    # ============================================================
    # INPUT DE ÁUDIO
    # ============================================================

    @staticmethod
    def validate_audio_input(ref_audio: Any) -> None:
        """
        Valida entrada de áudio sem tentar interpretá-la.

        Aceitamos:
            - str / Path
            - bytes / bytearray
            - file-like com read()

        O próprio Qwen aceita caminhos e outros formatos de referência.
        """
        if isinstance(ref_audio, (str, Path)):
            path = Path(ref_audio)

            if not path.exists():
                raise FileNotFoundError(
                    f"Arquivo de referência não encontrado:\n{path}"
                )

            if not path.is_file():
                raise ValueError(
                    f"O caminho não aponta para um arquivo:\n{path}"
                )

            return

        if isinstance(ref_audio, (bytes, bytearray)):
            if len(ref_audio) == 0:
                raise ValueError("O arquivo de referência está vazio.")
            return

        if hasattr(ref_audio, "read"):
            return

        if isinstance(ref_audio, tuple) and len(ref_audio) == 2:
            return

        raise TypeError(
            "ref_audio precisa ser caminho, bytes, file-like "
            "ou tuple (numpy_array, sample_rate)."
        )

    @staticmethod
    def materialize_audio_input(
        ref_audio: Any,
        *,
        suffix: str = ".wav",
    ) -> tuple[Any, Optional[Path]]:
        """
        Converte bytes/file-like em arquivo temporário dentro de
        ./outputs/. Caminhos existentes são retornados diretamente.

        O arquivo temporário é de propósito simples: isso deixa a futura
        UI livre para receber drag-and-drop e entregar o arquivo ao backend.
        """
        if isinstance(ref_audio, (str, Path)):
            return str(ref_audio), None

        if isinstance(ref_audio, tuple) and len(ref_audio) == 2:
            return ref_audio, None

        if isinstance(ref_audio, (bytes, bytearray)):
            raw = bytes(ref_audio)
        elif hasattr(ref_audio, "read"):
            raw = ref_audio.read()
        else:
            raise TypeError("Formato de áudio não suportado.")

        if not raw:
            raise ValueError("O áudio recebido está vazio.")

        filename = (
            OUTPUT_DIRECTORY
            / f".qwen_ref_{int(time.time() * 1000)}{suffix}"
        )

        filename.write_bytes(raw)
        return str(filename), filename

    # ============================================================
    # SAVE AUDIO
    # ============================================================

    def save_audio(
        self,
        wav: Any,
        sample_rate: int,
        output_path: str | Path,
    ) -> Path:
        _, sf = import_runtime()

        path = Path(output_path)

        if not path.is_absolute():
            path = self.output_dir / path

        path.parent.mkdir(parents=True, exist_ok=True)

        sf.write(
            str(path),
            wav,
            sample_rate,
        )

        return path

    # ============================================================
    # GENERATION CORE
    # ============================================================

    @staticmethod
    def audio_duration(wav: Any, sample_rate: int) -> float:
        try:
            return len(wav) / float(sample_rate)
        except Exception:
            return 0.0

    def _finish_generation(
        self,
        *,
        wav: Any,
        sample_rate: int,
        started: float,
        output_path: str | Path,
        request_id: Optional[str],
        details: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        elapsed = time.perf_counter() - started
        duration = self.audio_duration(wav, sample_rate)

        rtf = (
            elapsed / duration
            if duration > 0
            else float("inf")
        )

        saved = self.save_audio(
            wav,
            sample_rate,
            output_path,
        )

        model_name = "Desconhecido"
        if self.model_key in MODELS:
            model_name = MODELS[self.model_key]["name"]

        # Interface Visual da Geração Concluída
        print("\n" + "╭" + "─" * 50 + "╮")
        print(f"│{'GERAÇÃO CONCLUÍDA':^50}│")
        print("├" + "─" * 50 + "┤")
        print(f"│ Modelo:      {model_name:<35} │")
        print(f"│ Áudio:       {duration:>7.2f} s {' ':<28} │")
        print(f"│ Geração:     {elapsed:>7.2f} s {' ':<28} │")
        print(f"│ RTF:         {rtf:>7.2f} {' ':<30} │")
        print(f"│ Sample rate: {sample_rate:>7} Hz {' ':<27} │")
        print(f"│ Arquivo:     {str(saved):<35} │")
        print("╰" + "─" * 50 + "╯\n")

        result = {
            "path": str(saved),
            "sample_rate": sample_rate,
            "duration": duration,
            "generation_time": elapsed,
            "rtf": rtf,
            "request_id": request_id,
        }

        if details:
            result.update(details)

        self.last_generation = result

        self.emit(
            STATUS_READY,
            "Tudo pronto. Áudio gerado.",
            progress=1.0,
            request_id=request_id,
            details=result,
        )

        return result

    def _generation_error(
        self,
        exc: Exception,
        *,
        request_id: Optional[str],
    ) -> None:
        self.emit(
            STATUS_ERROR,
            "Algo deu errado durante a geração.",
            request_id=request_id,
            details={
                "exception": repr(exc),
                "traceback": traceback.format_exc(),
            },
        )

    # ============================================================
    # CUSTOMVOICE
    # ============================================================

    def generate_custom_voice(
        self,
        text: str,
        *,
        language: str = "Portuguese",
        speaker: str = "Aiden",
        instruct: Optional[str] = None,
        output_path: str | Path = "output_custom.wav",
        request_id: Optional[str] = None,
        **generation_kwargs: Any,
    ) -> dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Nenhum modelo carregado.")

        if self.model_type != "customvoice":
            raise RuntimeError(
                "O modelo atual não é CustomVoice."
            )

        if not text or not text.strip():
            raise ValueError("O texto está vazio.")

        model_info = MODELS[self.model_key]

        if instruct and not model_info["supports_instruct"]:
            print(
                "[AVISO] Este modelo não possui instruction control "
                "oficial. O instruct será ignorado."
            )
            instruct = None

        self.clear_cancel()

        self.emit(
            STATUS_ANALYZING,
            "Estou analisando a solicitação...",
            progress=0.05,
            request_id=request_id,
        )

        self.emit(
            STATUS_THINKING,
            "Estou preparando os parâmetros de voz...",
            progress=0.10,
            request_id=request_id,
        )

        self._check_cancel()

        self.emit(
            STATUS_GENERATING,
            "Estou gerando o áudio...",
            progress=0.20,
            request_id=request_id,
        )

        print()
        print("=" * 82)
        print("GERAÇÃO: CUSTOMVOICE")
        print("=" * 82)
        print(f"Modelo:   {model_info['name']}")
        print(f"Idioma:   {language}")
        print(f"Speaker:  {speaker}")
        print(f"Instruct: {instruct or '(nenhum)'}")
        print()
        print("Texto:")
        print(text)

        started = time.perf_counter()

        try:
            import torch

            kwargs: dict[str, Any] = {
                "text": text,
                "language": language,
                "speaker": speaker,
            }

            if instruct:
                kwargs["instruct"] = instruct

            kwargs.update(generation_kwargs)

            with torch.inference_mode():
                wavs, sample_rate = (
                    self.model.generate_custom_voice(**kwargs)
                )

            self._check_cancel()

            wav = wavs[0]

            return self._finish_generation(
                wav=wav,
                sample_rate=sample_rate,
                started=started,
                output_path=output_path,
                request_id=request_id,
                details={
                    "mode": "customvoice",
                    "model": model_info["name"],
                    "language": language,
                    "speaker": speaker,
                    "instruct": instruct,
                },
            )

        except Exception as exc:
            self._generation_error(
                exc,
                request_id=request_id,
            )
            raise

    # ============================================================
    # VOICEDESIGN
    # ============================================================

    def generate_voice_design(
        self,
        text: str,
        *,
        language: str = "Portuguese",
        instruct: str,
        output_path: str | Path = "output_voicedesign.wav",
        request_id: Optional[str] = None,
        **generation_kwargs: Any,
    ) -> dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Nenhum modelo carregado.")

        if self.model_type != "voicedesign":
            raise RuntimeError(
                "O modelo atual não é VoiceDesign."
            )

        if not text or not text.strip():
            raise ValueError("O texto está vazio.")

        if not instruct or not instruct.strip():
            raise ValueError(
                "VoiceDesign precisa de uma descrição da voz."
            )

        self.clear_cancel()

        self.emit(
            STATUS_ANALYZING,
            "Estou analisando a descrição da voz...",
            progress=0.05,
            request_id=request_id,
        )

        self.emit(
            STATUS_THINKING,
            "Estou preparando a voz que você descreveu...",
            progress=0.10,
            request_id=request_id,
        )

        self._check_cancel()

        self.emit(
            STATUS_GENERATING,
            "Estou gerando a voz e o áudio...",
            progress=0.20,
            request_id=request_id,
        )

        print()
        print("=" * 82)
        print("GERAÇÃO: VOICEDESIGN")
        print("=" * 82)
        print(f"Idioma: {language}")
        print()
        print("Descrição da voz:")
        print(instruct)
        print()
        print("Texto:")
        print(text)

        started = time.perf_counter()

        try:
            import torch

            kwargs = {
                "text": text,
                "language": language,
                "instruct": instruct,
            }

            kwargs.update(generation_kwargs)

            with torch.inference_mode():
                wavs, sample_rate = (
                    self.model.generate_voice_design(**kwargs)
                )

            self._check_cancel()

            wav = wavs[0]

            return self._finish_generation(
                wav=wav,
                sample_rate=sample_rate,
                started=started,
                output_path=output_path,
                request_id=request_id,
                details={
                    "mode": "voicedesign",
                    "model": MODELS[self.model_key]["name"],
                    "language": language,
                    "instruct": instruct,
                },
            )

        except Exception as exc:
            self._generation_error(
                exc,
                request_id=request_id,
            )
            raise

    # ============================================================
    # VOICE CLONE
    # ============================================================

    def generate_voice_clone(
        self,
        text: str,
        *,
        language: str = "Portuguese",
        ref_audio: Any,
        ref_text: str,
        output_path: str | Path = "output_clone.wav",
        x_vector_only_mode: bool = False,
        request_id: Optional[str] = None,
        **generation_kwargs: Any,
    ) -> dict[str, Any]:
        if self.model is None:
            raise RuntimeError("Nenhum modelo carregado.")

        if self.model_type != "base":
            raise RuntimeError(
                "O modelo atual não é Base."
            )

        if not text or not text.strip():
            raise ValueError("O texto está vazio.")

        self.validate_audio_input(ref_audio)

        if not x_vector_only_mode and not ref_text.strip():
            raise ValueError(
                "ref_text é obrigatório quando "
                "x_vector_only_mode=False."
            )

        self.clear_cancel()

        # --------------------------------------------------------
        # Arquivo vindo da futura UI
        # --------------------------------------------------------

        self.emit(
            STATUS_ANALYZING,
            "Estou analisando o arquivo de referência...",
            progress=0.05,
            request_id=request_id,
            details={
                "has_reference_audio": True,
            },
        )

        self._check_cancel()

        materialized_path: Optional[Path] = None

        try:
            ref_audio_for_qwen, materialized_path = (
                self.materialize_audio_input(ref_audio)
            )

            self.emit(
                STATUS_ANALYZING,
                "Arquivo recebido. Preparando a referência para o Qwen...",
                progress=0.12,
                request_id=request_id,
            )

            self.emit(
                STATUS_THINKING,
                "Estou preparando a voz de referência...",
                progress=0.18,
                request_id=request_id,
            )

            self._check_cancel()

            self.emit(
                STATUS_GENERATING,
                "Estou gerando o áudio com a voz de referência...",
                progress=0.25,
                request_id=request_id,
            )

            print()
            print("=" * 82)
            print("GERAÇÃO: VOICE CLONE")
            print("=" * 82)
            print(f"Modelo:  {MODELS[self.model_key]['name']}")
            print(f"Idioma:  {language}")
            print(f"Ref:     {ref_audio_for_qwen}")

            print()
            print("Texto da referência:")
            print(ref_text)

            print()
            print("Texto novo:")
            print(text)

            started = time.perf_counter()

            import torch

            kwargs = {
                "text": text,
                "language": language,
                "ref_audio": ref_audio_for_qwen,
                "ref_text": ref_text,
                "x_vector_only_mode": x_vector_only_mode,
            }

            kwargs.update(generation_kwargs)

            with torch.inference_mode():
                wavs, sample_rate = (
                    self.model.generate_voice_clone(**kwargs)
                )

            self._check_cancel()

            wav = wavs[0]

            return self._finish_generation(
                wav=wav,
                sample_rate=sample_rate,
                started=started,
                output_path=output_path,
                request_id=request_id,
                details={
                    "mode": "voice_clone",
                    "model": MODELS[self.model_key]["name"],
                    "language": language,
                    "ref_text": ref_text,
                    "x_vector_only_mode": x_vector_only_mode,
                    "reference_path": str(ref_audio_for_qwen),
                },
            )

        except Exception as exc:
            self._generation_error(
                exc,
                request_id=request_id,
            )
            raise

        finally:
            # Remove apenas os temporários que o backend criou.
            if materialized_path is not None:
                try:
                    materialized_path.unlink(missing_ok=True)
                except Exception:
                    pass

    # ============================================================
    # DIAGNÓSTICO
    # ============================================================

    def diagnostics(self) -> dict[str, Any]:
        """
        Retorna informações úteis para a futura UI / painel de diagnóstico.
        """
        result = {
            "backend_version": VERSION,
            "python": sys.version,
            "platform": sys.platform,
            "device": self.device,
            "dtype": self.dtype_name,
            "attention": self.attention,
            "hf_cache_dir": str(get_hf_cache_dir()),
            "model": self.status(),
        }

        try:
            import torch

            result["torch_version"] = torch.__version__
            result["cuda_version"] = torch.version.cuda
            result["cuda_available"] = torch.cuda.is_available()

        except Exception as exc:
            result["torch_error"] = repr(exc)

        try:
            import qwen_tts

            result["qwen_tts_version"] = getattr(
                qwen_tts,
                "__version__",
                "unknown",
            )
        except Exception as exc:
            result["qwen_tts_error"] = repr(exc)

        return result

    def print_diagnostics(self) -> None:
        data = self.diagnostics()

        print()
        print("=" * 82)
        print("DIAGNÓSTICO")
        print("=" * 82)

        for key, value in data.items():
            print(f"{key}: {value}")

        print("=" * 82)


# ================================================================
# CLI
# ================================================================

HELP_TEXT = r"""
COMANDOS
--------

  ajuda
      Mostra esta tela.

  modelos
      Lista os 5 modelos oficiais.

  baixar
      Escolhe um modelo para baixar.

  carregar
      Escolhe um modelo para carregar.

  descarregar
      Descarrega o modelo atual e limpa VRAM.

  status
      Mostra o estado atual do backend.

  gpu
      Mostra informações da GPU/VRAM.

  diagnostico
      Mostra versões e ambiente.

  custom
      Geração com CustomVoice.

  design
      Geração com VoiceDesign.

  clone
      Voice cloning usando arquivo de referência.

  cancelar
      Solicita cancelamento da operação atual.

  sair
      Fecha o backend.

ATALHOS
--------

Você também pode digitar diretamente o nome do modelo:

  1.7b customvoice
  1.7b voicedesign
  1.7b base
  0.6b customvoice
  0.6b base

A entrada é case-insensitive.

Exemplo:

  QWEN
  qwen
  QwEn

são normalizados antes da comparação.
"""


def cli_choose_model(prompt: str) -> Optional[str]:
    backend = GLOBAL_BACKEND

    print()
    backend.print_models()

    print()
    print(prompt)

    raw = input("> ")
    key = resolve_model(raw)

    if key is None:
        print(
            f"[ERRO] Modelo não reconhecido: {raw!r}"
        )
        return None

    return key


def cli_download() -> None:
    key = cli_choose_model(
        "Digite o modelo que deseja baixar:"
    )

    if key is None:
        return

    try:
        GLOBAL_BACKEND.download_model(key)
    except Exception:
        traceback.print_exc()


def cli_load() -> None:
    key = cli_choose_model(
        "Digite o modelo que deseja carregar:"
    )

    if key is None:
        return

    # Verificação inteligente de disponibilidade
    is_available = is_model_downloaded(key)

    print()
    print("Escolha o dtype:")
    print("  [1] FP32")
    print("  [2] FP16")
    print("  [3] BF16")

    raw_dtype = normalize(input("> "))

    dtype_map = {
        "1": "float32",
        "2": "float16",
        "3": "bfloat16",
        "fp32": "float32",
        "float32": "float32",
        "fp16": "float16",
        "float16": "float16",
        "bf16": "bfloat16",
        "bfloat16": "bfloat16",
    }

    dtype = dtype_map.get(raw_dtype, "float32")

    # Fluxo interativo caso o modelo não esteja disponível
    if not is_available:
        print(f"\n[AVISO] O modelo {MODELS[key]['name']} não foi encontrado localmente.")
        print("Deseja baixar e preparar o modelo agora?")
        confirm = input("(s/n) > ").strip().lower()

        if confirm != "s":
            print("[CANCELADO] Carregamento interrompido.")
            return

        try:
            GLOBAL_BACKEND.download_model(key)
        except Exception:
            traceback.print_exc()
            return

    # Carrega automaticamente após baixar ou se já existia
    try:
        GLOBAL_BACKEND.load_model(
            key,
            dtype=dtype,
        )
    except Exception:
        traceback.print_exc()


def cli_custom() -> None:
    backend = GLOBAL_BACKEND

    if backend.model is None:
        print("[ERRO] Carregue um CustomVoice primeiro.")
        return

    if backend.model_type != "customvoice":
        print("[ERRO] O modelo atual não é CustomVoice.")
        return

    print()
    text = input("Texto:\n> ")

    language = input(
        "Idioma [Portuguese]:\n> "
    ).strip() or "Portuguese"

    speakers = backend.get_speakers()

    print()
    print("Speakers:")
    for speaker in speakers:
        print(f"  - {speaker}")

    speaker = input("\nSpeaker:\n> ").strip()

    instruct = input(
        "\nInstruct [vazio = nenhum]:\n> "
    ).strip() or None

    try:
        result = backend.generate_custom_voice(
            text=text,
            language=language,
            speaker=speaker,
            instruct=instruct,
        )

        # Interação para conversão MP3
        if result and "path" in result:
            ask_for_mp3_conversion(result["path"])

    except Exception:
        traceback.print_exc()


def cli_design() -> None:
    backend = GLOBAL_BACKEND

    if backend.model is None:
        print("[ERRO] Carregue o VoiceDesign primeiro.")
        return

    if backend.model_type != "voicedesign":
        print("[ERRO] O modelo atual não é VoiceDesign.")
        return

    text = input("\nTexto:\n> ")

    language = input(
        "Idioma [Portuguese]:\n> "
    ).strip() or "Portuguese"

    instruct = input(
        "\nDescrição da voz:\n> "
    ).strip()

    try:
        result = backend.generate_voice_design(
            text=text,
            language=language,
            instruct=instruct,
        )

        # Interação para conversão MP3
        if result and "path" in result:
            ask_for_mp3_conversion(result["path"])

    except Exception:
        traceback.print_exc()


def cli_clone() -> None:
    backend = GLOBAL_BACKEND

    if backend.model is None:
        print("[ERRO] Carregue um modelo Base primeiro.")
        return

    if backend.model_type != "base":
        print("[ERRO] O modelo atual não é Base.")
        return

    print()
    text = input("Texto novo:\n> ")

    language = input(
        "Idioma [Portuguese]:\n> "
    ).strip() or "Portuguese"

    ref_audio = input(
        "\nCaminho do áudio de referência:\n> "
    ).strip()

    ref_text = input(
        "\nTranscrição do áudio de referência:\n> "
    ).strip()

    try:
        result = backend.generate_voice_clone(
            text=text,
            language=language,
            ref_audio=ref_audio,
            ref_text=ref_text,
        )

        # Interação para conversão MP3
        if result and "path" in result:
            ask_for_mp3_conversion(result["path"])

    except Exception:
        traceback.print_exc()


def ask_for_mp3_conversion(wav_path: str) -> None:
    """
    Pergunta ao usuário da CLI se deseja converter o WAV recém-gerado em MP3.
    """
    print(f"Converter WAV em MP3? [S/n]: ", end="")
    confirm = input().strip().lower()

    if confirm not in ("", "s", "sim", "y", "yes"):
        return

    print(f"\n[MP3] Convertendo WAV...")

    success, result = audio_converter.convert_wav_to_mp3(wav_path)

    if success:
        print(f"[MP3] Concluído.")
        print(f"[MP3] Arquivo: {result}")
    else:
        print(f"[MP3] Erro: {result}")
        if not audio_converter.is_ffmpeg_available():
            print(f"[MP3] Dica: FFmpeg não encontrado. O WAV continua disponível em:")
            print(f"      {wav_path}")


def print_cli_banner() -> None:
    print()
    print("=" * 82)
    print(f" {APP_NAME} v{VERSION}")
    print("=" * 82)

    print(
        "Backend modular iniciado. "
        "A futura UI poderá usar o mesmo motor."
    )

    print(
        "Digite 'ajuda' para ver os comandos."
    )

    print()


def run_cli() -> None:
    print_cli_banner()

    while True:
        try:
            command = normalize(
                input("qwen3-tts> ")
            )

        except KeyboardInterrupt:
            print()
            print("[BACKEND] Encerrando...")
            GLOBAL_BACKEND.unload_model()
            break

        except EOFError:
            GLOBAL_BACKEND.unload_model()
            break

        if not command:
            continue

        # --------------------------------------------------------
        # HELP
        # --------------------------------------------------------

        if command in {"ajuda", "help", "?"}:
            print(HELP_TEXT)
            continue

        # --------------------------------------------------------
        # MODELOS
        # --------------------------------------------------------

        if command in {
            "modelos",
            "models",
            "listar",
            "list",
        }:
            GLOBAL_BACKEND.print_models()
            continue

        # --------------------------------------------------------
        # DOWNLOAD
        # --------------------------------------------------------

        if command in {
            "baixar",
            "download",
        }:
            cli_download()
            continue

        # --------------------------------------------------------
        # LOAD
        # --------------------------------------------------------

        if command in {
            "carregar",
            "load",
        }:
            cli_load()
            continue

        # --------------------------------------------------------
        # UNLOAD
        # --------------------------------------------------------

        if command in {
            "descarregar",
            "unload",
            "liberar",
        }:
            try:
                GLOBAL_BACKEND.unload_model()
            except Exception:
                traceback.print_exc()
            continue

        # --------------------------------------------------------
        # STATUS
        # --------------------------------------------------------

        if command in {
            "status",
            "estado",
        }:
            GLOBAL_BACKEND.print_status()
            continue

        # --------------------------------------------------------
        # GPU
        # --------------------------------------------------------

        if command in {"gpu", "vram"}:
            print_gpu_info()
            continue

        # --------------------------------------------------------
        # DIAGNÓSTICO
        # --------------------------------------------------------

        if command in {
            "diagnostico",
            "diagnóstico",
            "diag",
            "debug",
        }:
            GLOBAL_BACKEND.print_diagnostics()
            continue

        # --------------------------------------------------------
        # CUSTOM
        # --------------------------------------------------------

        if command in {
            "custom",
            "customvoice",
            "tts",
        }:
            cli_custom()
            continue

        # --------------------------------------------------------
        # DESIGN
        # --------------------------------------------------------

        if command in {
            "design",
            "voicedesign",
            "voice design",
        }:
            cli_design()
            continue

        # --------------------------------------------------------
        # CLONE
        # --------------------------------------------------------

        if command in {
            "clone",
            "voiceclone",
            "voice clone",
        }:
            cli_clone()
            continue

        # --------------------------------------------------------
        # CANCEL
        # --------------------------------------------------------

        if command in {
            "cancelar",
            "cancel",
        }:
            GLOBAL_BACKEND.request_cancel()
            print("[BACKEND] Cancelamento solicitado.")
            continue

        # --------------------------------------------------------
        # EXIT
        # --------------------------------------------------------

        if command in {
            "sair",
            "exit",
            "quit",
        }:
            print("[BACKEND] Encerrando...")
            try:
                GLOBAL_BACKEND.unload_model()
            finally:
                break

        # --------------------------------------------------------
        # DIRECT MODEL ALIAS
        # --------------------------------------------------------

        model_key = resolve_model(command)

        if model_key is not None:
            try:
                GLOBAL_BACKEND.load_model(
                    model_key,
                    dtype=GLOBAL_BACKEND.dtype_name,
                )
            except Exception:
                traceback.print_exc()
            continue

        # --------------------------------------------------------
        # UNKNOWN
        # --------------------------------------------------------

        print(
            f"[ERRO] Comando desconhecido: {command!r}"
        )
        print("Digite 'ajuda'.")


# ================================================================
# GLOBAL INSTANCE
# ================================================================
#
# A UI futura poderá:
#
#   from qwen3_tts_backend import backend
#
# e então:
#
#   backend.add_listener(...)
#   backend.load_model(...)
#   backend.generate_custom_voice(...)
#
# ================================================================

GLOBAL_BACKEND = Qwen3TTSBackend()


# Alias amigável para a UI futura.
backend = GLOBAL_BACKEND


# ================================================================
# FUNÇÕES DE CONVENIÊNCIA PARA A UI
# ================================================================

def load_model(model_name: str, **kwargs: Any) -> Any:
    return GLOBAL_BACKEND.load_model(model_name, **kwargs)


def unload_model() -> bool:
    return GLOBAL_BACKEND.unload_model()


def download_model(model_name: str, **kwargs: Any) -> Path:
    return GLOBAL_BACKEND.download_model(
        model_name,
        **kwargs,
    )


def generate_custom_voice(
    text: str,
    **kwargs: Any,
) -> dict[str, Any]:
    return GLOBAL_BACKEND.generate_custom_voice(
        text,
        **kwargs,
    )


def generate_voice_design(
    text: str,
    **kwargs: Any,
) -> dict[str, Any]:
    return GLOBAL_BACKEND.generate_voice_design(
        text,
        **kwargs,
    )


def generate_voice_clone(
    text: str,
    **kwargs: Any,
) -> dict[str, Any]:
    return GLOBAL_BACKEND.generate_voice_clone(
        text,
        **kwargs,
    )


def add_event_listener(listener: EventListener) -> None:
    GLOBAL_BACKEND.add_listener(listener)


def remove_event_listener(listener: EventListener) -> None:
    GLOBAL_BACKEND.remove_listener(listener)


def request_cancel() -> None:
    GLOBAL_BACKEND.request_cancel()


def get_status() -> dict[str, Any]:
    return GLOBAL_BACKEND.status()


def list_models() -> list[dict[str, Any]]:
    return GLOBAL_BACKEND.list_models()


# ================================================================
# DEMONSTRAÇÃO DE EVENTOS
# ================================================================
#
# Não é obrigatória para uso.
#
# Exemplo de listener que uma UI poderia usar:
#
# def minha_ui(event):
#     if event.status == "loading":
#         label.setText(event.message)
#
# backend.add_listener(minha_ui)
#
# ================================================================


def _terminal_event_listener(event: BackendEvent) -> None:
    """
    Mantido aqui como exemplo documental.
    O CLI já imprime os eventos automaticamente.
    """
    pass


# ================================================================
# MAIN
# ================================================================

if __name__ == "__main__":
    try:
        run_cli()

    except Exception:
        print()
        print("=" * 82)
        print("ERRO FATAL DO BACKEND")
        print("=" * 82)

        traceback.print_exc()

        try:
            GLOBAL_BACKEND.unload_model()
        except Exception:
            pass

        raise

# Isso foi gerado por IA, o meu trabalho foi pesquisar, e insistir por um grande tempo para TODOS modelos funcionarem com uma tolerancia maior
# Não garanto que funcione em todos computadores
# Recomendo fortemente: 4GB DE VRAM, no modelo 0.6B, e 8GB DE VRAM no modelo 1.7B, para que funcione de forma aceitavel
# Vocês podem brincar com esse script se quiser, sejam felizes!