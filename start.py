from ukrainian_tts.tts import TTS, Voices, Stress
import IPython.display as ipd
from gtts import gTTS
# Removed os, traceback, soundfile, numpy as they are not strictly needed for the core fix based on your example

def generate_speech(text_file, language):
    try:
        with open(text_file, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {text_file}")
        return None

    output_file = None # Initialize

    if language == "uk":
        # Define the output file path first
        output_file = "../output_uk.wav"
        try:
            tts = TTS(device="cpu") # can try gpu, mps
            # *** Use the correct method: Open file and pass handle to tts.tts ***
            with open(output_file, mode="wb") as audio_file_handle:
                _, output_text = tts.tts(text,
                                         Voices.Lada.value,
                                         Stress.Dictionary.value,
                                         audio_file_handle) # <-- Pass the file handle
            print("Accented text (Ukrainian):", output_text)
            # No explicit save needed here, tts.tts handled it
        except Exception as e:
            print(f"Error during Ukrainian TTS generation: {e}")
            return None # Return None on error

    elif language == "en":
        # Keep the original logic for English
        output_file = "../output_en.wav"
        try:
            tts_en = gTTS(text=text, lang='en')
            tts_en.save(output_file)
        except Exception as e:
            print(f"Error during English TTS generation: {e}")
            return None # Return None on error

    # Removed the explicit check for unsupported language from the original code
    # as it wasn't present, but added error handling above.
    # If language is neither 'uk' nor 'en', output_file remains None.

    return output_file # Return the path (or None if error occurred)

# --- Original main script logic ---
uk_text_file = "../textUK.txt"
en_text_file = "../textEN.txt"

uk_output_file = generate_speech(uk_text_file, "uk")
en_output_file = generate_speech(en_text_file, "en")

if uk_output_file:
    print(f"Ukrainian speech saved to: {uk_output_file}")
    # This line should now work as the file is created by tts.tts
    ipd.Audio(filename=uk_output_file)
else:
    # Added simple feedback if file generation failed
    print("Ukrainian audio file was not generated successfully.")


if en_output_file:
    print(f"English speech saved to: {en_output_file}")
    ipd.Audio(filename=en_output_file)
else:
    # Added simple feedback if file generation failed
    print("English audio file was not generated successfully.")