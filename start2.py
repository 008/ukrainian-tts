import base64
import mimetypes
import os
import struct
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydub import AudioSegment
from glob import glob
from tqdm import tqdm
load_dotenv()

# Set these flags to enable/disable generation
GENERATE_UK = True
GENERATE_EN = False

def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict:
    bits_per_sample = 16
    rate = 24000
    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass
    return {"bits_per_sample": bits_per_sample, "rate": rate}

def convert_wav_to_mp3(wav_path, bitrate):
    mp3_path = wav_path.replace(".wav", ".mp3")
    try:
        audio = AudioSegment.from_wav(wav_path)
        audio.export(mp3_path, format="mp3", bitrate=bitrate)
        print(f"Converted {wav_path} to {mp3_path} at {bitrate}.")
        os.remove(wav_path)
        print(f"Removed original WAV file: {wav_path}")
    except Exception as e:
        print(f"Error converting {wav_path} to MP3: {e}")

def generate_speech(text_file, output_file, voice_name="Zephyr"):
    try:
        with open(text_file, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {text_file}")
        return None
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = "gemini-2.5-flash-preview-tts"
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=text)],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        ),
    )
    audio_chunks = []
    print("Generating speech (this may take a while)...")
    for chunk in tqdm(client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config
    ), desc="Progress", unit="chunk"):
        if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
            part = chunk.candidates[0].content.parts[0]
            if hasattr(part, "inline_data") and part.inline_data:
                inline_data = part.inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                if file_extension is None:
                    file_extension = ".wav"
                    data_buffer = convert_to_wav(inline_data.data, inline_data.mime_type)
                save_binary_file(f"{output_file}{file_extension}", data_buffer)
                return f"{output_file}{file_extension}"
            elif hasattr(part, "text"):
                print(part.text)
        else:
            print(chunk.text)
    return None


if __name__ == "__main__":
    uk_text_file = "../textUK.txt"
    en_text_file = "../textEN.txt"
    uk_output_file = "../output_uk"
    en_output_file = "../output_en"
    if GENERATE_UK:
        print("Generating Ukrainian speech...")
        uk_result = generate_speech(uk_text_file, uk_output_file, voice_name="Zephyr")
        if uk_result:
            print(f"Ukrainian speech ready: {uk_result}")
        else:
            print("Ukrainian audio file was not generated successfully.")
    else:
        uk_result = None
    if GENERATE_EN:
        print("Generating English speech...")
        en_result = generate_speech(en_text_file, en_output_file, voice_name="Zephyr")
        if en_result:
            print(f"English speech ready: {en_result}")
        else:
            print("English audio file was not generated successfully.")
    else:
        en_result = None
    mp3_bitrate = "65k"  # Set your desired MP3 bitrate here (e.g., "128k", "192k", "256k")
    # Convert generated WAV files to MP3
    if uk_result and os.path.exists(uk_result):
        convert_wav_to_mp3(uk_result, mp3_bitrate)
    if en_result and os.path.exists(en_result):
        convert_wav_to_mp3(en_result, mp3_bitrate)