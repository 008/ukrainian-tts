# .venv-py310\Scripts\activate


from ukrainian_tts.tts import TTS, Voices, Stress
import IPython.display as ipd
from gtts import gTTS
from pydub import AudioSegment # <-- Import pydub
import os # <-- Useful for removing temp files
from glob import glob # Moved here for better organization

# --- GENERATION FLAGS ---
# Set to True to generate speech for that language, False to skip.
GENERATE_UKRAINIAN = False # Set this to False if you want to skip Ukrainian
GENERATE_ENGLISH = True    # Set this to True if you want English generation


def generate_speech(text_file, language, speed_factor=1.0): # <-- Added speed_factor
    """
    Generates speech from a text file for a specified language.
    language: "uk" for Ukrainian, "en" for English.
    speed_factor: Multiplier for English audio speed (1.0 for normal).
    """
    try:
        with open(text_file, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {text_file}")
        return None

    output_file = None

    if language == "uk":
        output_file = "../output_uk.wav"
        try:
            print(f"Generating Ukrainian speech from {text_file}...")
            tts = TTS(device="cpu")
            with open(output_file, mode="wb") as audio_file_handle:
                _, output_text = tts.tts(text,
                                         Voices.Lada.value,
                                         Stress.Dictionary.value,
                                         audio_file_handle)
            print("Accented text (Ukrainian):", output_text)
        except Exception as e:
            print(f"Error during Ukrainian TTS generation: {e}")
            return None

    elif language == "en":
        # Define a temporary path for the initial gTTS output
        temp_output_file = "../output_en_temp.mp3" # gTTS often prefers mp3
        final_output_file = "../output_en.wav"    # Your desired final format

        try:
            print(f"Generating English speech from {text_file}...")
            tts_en = gTTS(text=text, lang='en', slow=False) # slow=False is default, but good to be explicit
            tts_en.save(temp_output_file)

            # Post-process with pydub to change speed
            sound = AudioSegment.from_file(temp_output_file, format="mp3")

            if speed_factor != 1.0:
                print(f"Attempting to speed up English audio by {speed_factor}x...")
                # Speeding up might change the pitch.
                # For more advanced pitch-preserving speed-up, you might need more complex tools or libraries.
                # pydub's speedup is quite good for moderate changes.
                faster_sound = sound.speedup(playback_speed=speed_factor)
                faster_sound.export(final_output_file, format="wav")
                print(f"English speech saved to: {final_output_file} (sped up)")
            else:
                # If no speed change, just convert/copy to final destination
                sound.export(final_output_file, format="wav")
                print(f"English speech saved to: {final_output_file} (original speed)")

            output_file = final_output_file

        except Exception as e:
            print(f"Error during English TTS generation or processing: {e}")
            return None
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_output_file):
                try:
                    os.remove(temp_output_file)
                except Exception as e_rem:
                    print(f"Could not remove temporary file {temp_output_file}: {e_rem}")


    return output_file

# --- Main script logic ---
uk_text_file = "../textUK.txt"
en_text_file = "../textEN.txt"


# --- Ukrainian Generation ---
uk_output_file = None
if GENERATE_UKRAINIAN:
    uk_output_file = generate_speech(uk_text_file, "uk")
    if uk_output_file:
        print(f"Ukrainian speech ready: {uk_output_file}")
        # Note: ipd.Audio might only work in environments like Jupyter notebooks
        # ipd.Audio(filename=uk_output_file) # Display/play
    else:
        print("Ukrainian audio file was not generated successfully.")
else:
    print("Ukrainian speech generation skipped by user settings.")

print("-" * 30) # Separator for clarity

# --- English Generation ---
en_output_file = None
if GENERATE_ENGLISH:
    # Example: Make English voice 25% faster (1.25x)
    # You can adjust the speed_factor:
    # 1.0 = normal speed
    # 1.5 = 50% faster
    # 0.8 = 20% slower
    en_speed = 1.25
    en_output_file = generate_speech(en_text_file, "en", speed_factor=en_speed)
    if en_output_file:
        print(f"English speech ready: {en_output_file}")
        # Note: ipd.Audio might only work in environments like Jupyter notebooks
        # ipd.Audio(filename=en_output_file) # Display/play
    else:
        print("English audio file was not generated successfully.")
else:
    print("English speech generation skipped by user settings.")

print("-" * 30) # Separator for clarity

# --- WAV to MP3 conversion and cleanup ---
# This section will still run and convert any .wav files found,
# regardless of whether they were just generated or already existed.
mp3_bitrate = "65k"  # Set your desired MP3 bitrate here (e.g., "128k", "192k", "256k")

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

print("Checking for WAV files to convert to MP3 and clean up...")
# Find all resulting WAV files in the parent directory
wav_files = glob("../*.wav")
if wav_files:
    for wav_file in wav_files:
        convert_wav_to_mp3(wav_file, mp3_bitrate)
else:
    print("No WAV files found for conversion.")

print("\nScript finished.")