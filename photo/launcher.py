import os
import sys
import socket
import webbrowser
import subprocess
import time
from pathlib import Path

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port=7860):
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

def print_banner():
    print("=" * 50)
    print("       QWEN3-TTS LOCAL STUDIO")
    print("=" * 50)
    print("  Iniciando servidor local...")
    print("=" * 50)

def main():
    print_banner()

    port = find_available_port()
    print(f"\nSugerindo porta: {port}")

    try:
        user_port = input(f"Escolha a porta [{port}]: ").strip()
        if user_port:
            port = int(user_port)
    except ValueError:
        print("Porta inválida. Usando sugestão.")

    print(f"\nIniciando na porta {port}...")

    allow_lan = input("Permitir acesso pela rede local (LAN)? [s/N]: ").strip().lower() == 's'
    host = "0.0.0.0" if allow_lan else "127.0.0.1"

    # Inicia o uvicorn como um processo separado
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port), "--log-level", "warning"]

    # Abre o navegador após um curto delay
    url = f"http://localhost:{port}"
    print(f"O Studio será aberto em: {url}")

    # Inicia o servidor
    process = subprocess.Popen(cmd)

    time.sleep(2)
    webbrowser.open(url)

    print("\nServidor rodando. Feche esta janela para encerrar o Studio.")
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        print("\nStudio encerrado.")

if __name__ == "__main__":
    main()
