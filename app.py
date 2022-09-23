import tempfile

import gradio as gr

from TTS.utils.synthesizer import Synthesizer
import requests
from os.path import exists
from ukrainian_tts.formatter import preprocess_text
from datetime import datetime
from enum import Enum
import torch


class StressOption(Enum):
    AutomaticStress = "Автоматичні наголоси (за словником) 📖"
    AutomaticStressWithModel = "Автоматичні наголоси (за допомогою моделі) 🧮"


class VoiceOption(Enum):
    Olena = "Олена (жіночий) 👩"
    Mykyta = "Микита (чоловічий) 👨"
    Lada = "Лада (жіночий) 👩"
    Dmytro = "Дмитро (чоловічий) 👨"
    Olga = "Ольга (жіночий) 👩"


def download(url, file_name):
    if not exists(file_name):
        print(f"Downloading {file_name}")
        r = requests.get(url, allow_redirects=True)
        with open(file_name, "wb") as file:
            file.write(r.content)
    else:
        print(f"Found {file_name}. Skipping download...")


print("downloading uk/mykyta/vits-tts")
release_number = "v3.0.0"
model_link = f"https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}/model-inference.pth"
config_link = f"https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}/config.json"
speakers_link = f"https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}/speakers.pth"

model_path = "model.pth"
config_path = "config.json"
speakers_path = "speakers.pth"

download(model_link, model_path)
download(config_link, config_path)
download(speakers_link, speakers_path)

badge = (
    "https://visitor-badge-reloaded.herokuapp.com/badge?page_id=robinhad.ukrainian-tts"
)

synthesizer = Synthesizer(
    model_path,
    config_path,
    speakers_path,
    None,
    None,
)

if synthesizer is None:
    raise NameError("model not found")


def tts(text: str, voice: str, stress: str):
    print("============================")
    print("Original text:", text)
    print("Voice", voice)
    print("Stress:", stress)
    print("Time:", datetime.utcnow())
    autostress_with_model = (
        True if stress == StressOption.AutomaticStressWithModel.value else False
    )
    voice_mapping = {
        VoiceOption.Olena.value: "olena",
        VoiceOption.Mykyta.value: "mykyta",
        VoiceOption.Lada.value: "lada",
        VoiceOption.Dmytro.value: "dmytro",
        VoiceOption.Olga.value: "olga",
    }
    speaker_name = voice_mapping[voice]
    text = preprocess_text(text, autostress_with_model)
    text_limit = 7200
    text = (
        text if len(text) < text_limit else text[0:text_limit]
    )  # mitigate crashes on hf space
    print("Converted:", text)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
        with torch.no_grad():
            wavs = synthesizer.tts(text, speaker_name=speaker_name)
            synthesizer.save_wav(wavs, fp)
        return fp.name, text


with open("README.md") as file:
    article = file.read()
    article = article[article.find("---\n", 4) + 5::]


iface = gr.Interface(
    fn=tts,
    inputs=[
        gr.components.Textbox(
            label="Input",
            value="Введіть, будь ласка, своє р+ечення.",
        ),
        gr.components.Radio(
            label="Голос",
            choices=[option.value for option in VoiceOption],
            value=VoiceOption.Olena.value,
        ),
        gr.components.Radio(
            label="Наголоси",
            choices=[option.value for option in StressOption],
            value=StressOption.AutomaticStress.value
        ),
    ],
    outputs=[
        gr.components.Audio(label="Output"),
        gr.components.Textbox(label="Наголошений текст"),
    ],
    title="🐸💬🇺🇦 - Coqui TTS",
    description="Україномовний🇺🇦 TTS за допомогою Coqui TTS (щоб вручну поставити наголос, використовуйте + перед голосною)",
    article=article + f'\n  <center><img src="{badge}" alt="visitors badge"/></center>',
    examples=[
        [
            "Введіть, будь ласка, своє речення.",
            VoiceOption.Olena.value,
            StressOption.AutomaticStress.value,
        ],
        [
            "Введіть, будь ласка, своє речення.",
            VoiceOption.Mykyta.value,
            StressOption.AutomaticStress.value,
        ],
        [
            "Вв+едіть, будь ласка, св+оє реч+ення.",
            VoiceOption.Dmytro.value,
            StressOption.AutomaticStress.value,
        ],
        [
            "Привіт, як тебе звати?",
            VoiceOption.Olga.value,
            StressOption.AutomaticStress.value,
        ],
        [
            "Договір підписано 4 квітня 1949 року.",
            VoiceOption.Lada.value,
            StressOption.AutomaticStress.value,
        ],
    ],
)
iface.launch(enable_queue=True)
