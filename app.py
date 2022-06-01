import tempfile

import gradio as gr

from TTS.utils.synthesizer import Synthesizer
import requests
from os.path import exists
from formatter import preprocess_text
from datetime import datetime
from stress import sentence_to_stress
from enum import Enum
import torch

class StressOption(Enum):
    ManualStress = "Наголоси вручну"
    AutomaticStress = "Автоматичні наголоси (Beta)"


def download(url, file_name):
    if not exists(file_name):
        print(f"Downloading {file_name}")
        r = requests.get(url, allow_redirects=True)
        with open(file_name, 'wb') as file:
            file.write(r.content)
    else:
        print(f"Found {file_name}. Skipping download...")


print("downloading uk/mykyta/vits-tts")
release_number = "v2.0.0-beta"
model_link = f"https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}/model-inference.pth"
config_link = f"https://github.com/robinhad/ukrainian-tts/releases/download/{release_number}/config.json"

model_path = "model.pth"
config_path = "config.json"

download(model_link, model_path)
download(config_link, config_path)


synthesizer = Synthesizer(
    model_path, config_path, None, None, None,
)

if synthesizer is None:
    raise NameError("model not found")

def tts(text: str, stress: str):
    text = preprocess_text(text)
    text_limit = 1200
    text = text if len(text) < text_limit else text[0:text_limit] # mitigate crashes on hf space
    text = sentence_to_stress(text) if stress == StressOption.AutomaticStress.value else text
    print(text, stress, datetime.utcnow())

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
        with torch.no_grad():
            wavs = synthesizer.tts(text)
            synthesizer.save_wav(wavs, fp)
        return fp.name


iface = gr.Interface(
    fn=tts,
    inputs=[
        gr.inputs.Textbox(
            label="Input",
            default="Введ+іть, б+удь л+аска, сво+є р+ечення.",
        ),
        gr.inputs.Radio(
            label="Опції",
            choices=[option.value for option in StressOption],
        ),
    ],
    outputs=gr.outputs.Audio(label="Output"),
    title="🐸💬🇺🇦 - Coqui TTS",
    theme="huggingface",
    description="Україномовний🇺🇦 TTS за допомогою Coqui TTS (для наголосу використовуйте + перед голосною)",
    article="Якщо вам подобається, підтримайте за посиланням: [SUPPORT LINK](https://send.monobank.ua/jar/48iHq4xAXm),  " +
    "Github: [https://github.com/robinhad/ukrainian-tts](https://github.com/robinhad/ukrainian-tts)",
    examples=[
        ["Введ+іть, б+удь л+аска, сво+є р+ечення.", StressOption.ManualStress.value],
        ["Введіть, будь ласка, своє речення.", StressOption.ManualStress.value],
        ["Привіт, як тебе звати?", StressOption.AutomaticStress.value],
    ]
)
iface.launch(enable_queue=True, prevent_thread_lock=True)
