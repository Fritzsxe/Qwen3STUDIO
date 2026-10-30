import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

# ==============================================================================
# AUDIO CONVERTER MODULE (FFmpeg Wrapper)
# ==============================================================================
#
# Motor independente para conversão de áudio.
# Utiliza FFmpeg externo para codificação MP3 (libmp3lame).
#
# Licença FFmpeg (LGPL/GPL):
# Este módulo não contém código do FFmpeg, apenas o invoca via subprocess.
# Documentação oficial: https://ffmpeg.org/ffmpeg.html
# ==============================================================================

DEFAULT_MP3_DIR = Path(__file__).parent / "mp3out"

def find_ffmpeg() -> Optional[Path]:
    """
    Localiza o executável FFmpeg seguindo as prioridades:
    1. ferramentas locais do projeto (./tools/ffmpeg/ffmpeg.exe relativo ao script)
    2. PATH do sistema
    """
    # 1. Busca local relativa ao script
    script_dir = Path(__file__).parent
    local_path = script_dir / "tools" / "ffmpeg" / "ffmpeg.exe"

    if local_path.exists():
        return local_path.absolute()

    # 2. Busca no PATH do sistema
    path_executable = shutil.which("ffmpeg")
    if path_executable:
        return Path(path_executable)

    return None

def is_ffmpeg_available() -> bool:
    return find_ffmpeg() is not None

def get_ffmpeg_version() -> str:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return "Não encontrado"
    try:
        result = subprocess.run(
            [str(ffmpeg), "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        # Retorna a primeira linha da versão
        return result.stdout.splitlines()[0]
    except Exception:
        return "Erro ao obter versão"

def get_next_mp3_path(directory: Path = DEFAULT_MP3_DIR) -> Path:
    """
    Gera o caminho para o próximo arquivo numérico sequencial.
    Ex: 1.mp3, 2.mp3, ...
    """
    directory.mkdir(parents=True, exist_ok=True)

    # Lista arquivos .mp3 existentes
    existing_files = list(directory.glob("*.mp3"))
    existing_numbers = []

    for f in existing_files:
        try:
            num = int(f.stem)
            existing_numbers.append(num)
        except ValueError:
            continue

    # Encontra o primeiro número livre (buracos inclusos)
    next_num = 1
    if existing_numbers:
        # Se houver buracos, ou se quisermos apenas o maior + 1
        # O requisito pede: "escolher um número que ainda não exista"
        while next_num in existing_numbers:
            next_num += 1

    return directory / f"{next_num}.mp3"

def convert_wav_to_mp3(wav_path: str | Path) -> Tuple[bool, str]:
    """
    Converte WAV para MP3 usando as melhores configurações para voz (TTS).

    Configuração escolhida:
    - Encoder: libmp3lame
    - Bitrate: 64k (CBR para melhor compatibilidade com players web/mobile)
    - Channels: 1 (Mono, voz nativa)
    - Sample Rate: Preserva o original do WAV (normalmente 24kHz no Qwen3)

    Retorna: (Sucesso, Mensagem/Caminho)
    """
    wav_path = Path(wav_path)
    if not wav_path.exists():
        return False, f"Arquivo de entrada não encontrado: {wav_path}"

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return False, "Executável FFmpeg não encontrado no PATH ou pasta tools."

    output_path = get_next_mp3_path()

    # Comando FFmpeg seguro (lista de argumentos)
    # -y: sobrescrever (não deve ocorrer devido ao get_next_mp3_path, mas é boa prática)
    # -i: input
    # -c:a: codec audio
    # -b:a: bitrate audio
    # -ac: audio channels
    command = [
        str(ffmpeg),
        "-y",
        "-i", str(wav_path.absolute()),
        "-c:a", "libmp3lame",
        "-b:a", "64k",
        "-ac", "1",
        str(output_path.absolute())
    ]

    try:
        # Execução sem shell=True para evitar injeção
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and output_path.exists():
            return True, str(output_path)
        else:
            error_msg = result.stderr.splitlines()[-1] if result.stderr else "Erro desconhecido"
            return False, f"Falha na conversão: {error_msg}"

    except Exception as e:
        return False, f"Erro ao executar FFmpeg: {str(e)}"

if __name__ == "__main__":
    # Teste de diagnóstico
    print("--- Diagnóstico AudioConverter ---")
    print(f"FFmpeg encontrado: {find_ffmpeg() or 'NÃO'}")
    print(f"Versão: {get_ffmpeg_version()}")
    print(f"Disponível: {is_ffmpeg_available()}")
    print(f"Pasta MP3: {DEFAULT_MP3_DIR.absolute()}")
    print(f"Próximo arquivo: {get_next_mp3_path().name}")
