import os
import sys
import time

import torch
import soundfile as sf

from qwen_tts import Qwen3TTSModel


MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"


def main():
    print("=== Qwen3-TTS 0.6B | TESTE LIMPO ===")

    if not torch.cuda.is_available():
        print("CUDA não disponível.")
        return

    print("GPU:", torch.cuda.get_device_name(0))

    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        device_map="cuda:0",
        trust_remote_code=True,
        dtype=torch.float32,
        attn_implementation="sdpa",
    )

    print("Modelo carregado.")
    print("Modelo:", model.model.tts_model_size)
    print("Speakers:", model.get_supported_speakers())
    print("Languages:", model.get_supported_languages())

    text = "OPA! E AÍ?! Esse é o segundo teste desse text to speak, como foi? Sem vomitar? Hahah!"

    print("\nGerando...")
    start = time.time()

    with torch.inference_mode():
        wavs, sr = model.generate_custom_voice(
            text=text,
            language="auto",
            speaker="ono_anna",
        )

    torch.cuda.synchronize()

    elapsed = time.time() - start

    audio = wavs[0]

    if torch.is_tensor(audio):
        audio = audio.detach().cpu().numpy()

    duration = len(audio) / sr

    output = os.path.abspath("output.wav")

    sf.write(
        output,
        audio,
        sr,
    )

    print("\n=== RESULTADO ===")
    print("Arquivo:", output)
    print(f"Sample rate: {sr} Hz")
    print(f"Duração: {duration:.2f}s")
    print(f"Tempo: {elapsed:.2f}s")
    print(f"RTF: {elapsed / duration:.2f}")


if __name__ == "__main__":
    main()