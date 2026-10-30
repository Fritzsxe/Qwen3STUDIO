
import os
import sys
import time
import copy

import torch
import soundfile as sf


# ============================================================
# Qwen3-TTS 1.7B CustomVoice
# GTX 1650 4 GB
#
# IMPORTANTE:
# O modelo já foi baixado pelo Hugging Face.
# Não fazemos download manual.
# ============================================================


MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"

OUTPUT_FILE = "output_1.7b.wav"

TEXT = (
    "Mano, eu consigo fazer uma análise do áudio em si! "
    "Sem inventar emoção, sem meter o louco. "
    "Agora eu quero ver o que esse modelo consegue fazer!"
)

LANGUAGE = "Portuguese"
SPEAKER = "Aiden"

INSTRUCT = (
    "Speak naturally and expressively, with a lively and enthusiastic tone. "
    "Use natural pauses, pitch variation, and emotional emphasis. "
    "Do not sound robotic."
)


# ============================================================
# PATCH PARA:
#
# cannot pickle 'dict_keys' object
#
# O Qwen3-TTS expõe alguns dict_keys internamente.
# O deepcopy usado durante a quantização do Transformers/
# bitsandbytes não consegue serializar esse objeto no Python 3.12.
# ============================================================

try:
    copy._deepcopy_dispatch[type({}.keys())] = (
        lambda x, memo: list(x)
    )
except Exception as e:
    print("Aviso: não foi possível aplicar o patch dict_keys:")
    print(e)


# ============================================================
# IMPORTS
# ============================================================

try:
    from qwen_tts import Qwen3TTSModel
    from transformers import BitsAndBytesConfig

except ImportError as e:
    print("\nERRO: biblioteca ausente:")
    print(e)
    print("\nInstale as dependências necessárias.")
    sys.exit(1)


# ============================================================
# VRAM
# ============================================================

def print_vram(label):

    if not torch.cuda.is_available():
        return

    allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
    reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
    total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)

    print(
        f"[{label}] "
        f"VRAM: {allocated:.2f} GB alocada | "
        f"{reserved:.2f} GB reservada | "
        f"Total: {total:.2f} GB"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print("Qwen3-TTS 1.7B CustomVoice")
    print("INT8 + SDPA | GTX 1650 4GB")
    print("=" * 65)

    # --------------------------------------------------------
    # CUDA
    # --------------------------------------------------------

    if not torch.cuda.is_available():

        print("\nERRO: CUDA não está disponível.")
        return

    print("\nGPU:")
    print(torch.cuda.get_device_name(0))

    print_vram("Inicial")


    # --------------------------------------------------------
    # Quantização
    # --------------------------------------------------------

    print("\nConfigurando INT8...")

    quantization_config = BitsAndBytesConfig(
        load_in_8bit=True,
        llm_int8_threshold=6.0,
    )


    # --------------------------------------------------------
    # Carregamento
    #
    # O Hugging Face vai reutilizar o cache existente.
    # Não estamos mandando baixar o modelo novamente.
    # --------------------------------------------------------

    print("\nCarregando:")

    print(MODEL_ID)

    print(
        "\nSe o modelo já estiver no cache, "
        "nenhum download adicional será necessário."
    )

    start_load = time.time()

    try:

        model = Qwen3TTSModel.from_pretrained(
            MODEL_ID,

            device_map="cuda:0",

            trust_remote_code=True,

            quantization_config=quantization_config,

            attn_implementation="sdpa",
        )

    except torch.cuda.OutOfMemoryError:

        print("\n" + "=" * 65)
        print("ERRO: OUT OF MEMORY")
        print("=" * 65)

        print(
            "\nA GTX 1650 não conseguiu carregar o 1.7B "
            "nessa configuração."
        )

        print(
            "\nO modelo NÃO será baixado novamente."
        )

        return

    except Exception as e:

        print("\n" + "=" * 65)
        print("ERRO AO CARREGAR O MODELO")
        print("=" * 65)

        print(type(e).__name__)
        print(e)

        return


    load_time = time.time() - start_load

    print(
        f"\nModelo carregado em {load_time:.2f}s"
    )

    print_vram("Após carregamento")


    # --------------------------------------------------------
    # Informações
    # --------------------------------------------------------

    try:

        print("\nSpeakers:")
        print(model.get_supported_speakers())

        print("\nIdiomas:")
        print(model.get_supported_languages())

    except Exception as e:

        print(
            "\nAviso: não foi possível listar "
            "speakers/idiomas:"
        )

        print(e)


    # --------------------------------------------------------
    # GERAÇÃO
    # --------------------------------------------------------

    print("\n" + "=" * 65)
    print("GERAÇÃO")
    print("=" * 65)

    print("\nTexto:")
    print(TEXT)

    print("\nIdioma:", LANGUAGE)
    print("Speaker:", SPEAKER)

    print("\nInstruct:")
    print(INSTRUCT)

    print("\nGerando...")


    start_generation = time.time()

    try:

        with torch.inference_mode():

            wavs, sr = model.generate_custom_voice(
                text=TEXT,
                language=LANGUAGE,
                speaker=SPEAKER,
                instruct=INSTRUCT,
            )

        torch.cuda.synchronize()

    except torch.cuda.OutOfMemoryError:

        print("\n" + "=" * 65)
        print("ERRO: OUT OF MEMORY DURANTE A GERAÇÃO")
        print("=" * 65)

        print_vram("Após OOM")

        return

    except Exception as e:

        print("\nERRO durante a geração:")
        print(type(e).__name__)
        print(e)

        return


    generation_time = time.time() - start_generation


    # --------------------------------------------------------
    # ÁUDIO
    # --------------------------------------------------------

    audio = wavs[0]

    if torch.is_tensor(audio):

        audio = (
            audio
            .detach()
            .cpu()
            .numpy()
        )


    duration = len(audio) / sr

    rtf = (
        generation_time / duration
        if duration > 0
        else 0
    )


    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    output_path = os.path.abspath(
        OUTPUT_FILE
    )

    sf.write(
        output_path,
        audio,
        sr,
    )


    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print("\n" + "=" * 65)
    print("RESULTADO")
    print("=" * 65)

    print(f"Arquivo: {output_path}")
    print(f"Sample rate: {sr} Hz")
    print(f"Duração: {duration:.2f}s")
    print(
        f"Tempo de geração: "
        f"{generation_time:.2f}s"
    )
    print(f"RTF: {rtf:.2f}")

    print_vram("Final")

    print("\n🎙️ Geração concluída.")


if __name__ == "__main__":
    main()

