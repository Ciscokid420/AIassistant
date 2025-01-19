from vosk import Model, KaldiRecognizer
import pyaudio
import json
import sys
import os
import time
from collections import deque

def setup_vosk():
    model_path = "/home/cisco/Documents/Vosk/vosk-model-small-en-us-0.15"
    try:
        model = Model(model_path)
        print("Model loaded successfully")
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    return recognizer

def setup_audio():
    audio = pyaudio.PyAudio()
    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096
        )
        stream.start_stream()
        print("Audio stream initialized")
        return stream, audio
    except Exception as e:
        print(f"Error setting up audio: {e}")
        audio.terminate()
        sys.exit(1)

def is_silent(data):
    """Check if the audio data is silent"""
    return max(abs(int.from_bytes(data[i:i+2], 'little', signed=True)) 
               for i in range(0, len(data), 2)) < 500

def transcribe_after_wake_word(recognizer, audio_stream, wake_word="hey dexter"):
    transcribing = False
    output_file = "/home/cisco/Documents/llama/transcription/transcription.txt"
    last_sound_time = time.time()
    memory_buffer = deque()  # Ring buffer for storing text in memory
    print(f"Listening for wake word: '{wake_word}'...")

    while True:
        try:
            data = audio_stream.read(4096, exception_on_overflow=False)

            # Update last_sound_time if not silent
            if not is_silent(data):
                last_sound_time = time.time()

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                if text:
                    print("Heard:", text)

                    # Check for wake word if not already transcribing
                    if not transcribing and wake_word.lower() in text.lower():
                        transcribing = True
                        print(f"\nWake word detected! Starting transcription to {output_file}\n")
                        last_sound_time = time.time()  # Reset silence timer after wake word

                        # Clear memory buffer
                        memory_buffer.clear()
                        continue

                    # If we're transcribing, save the text in memory
                    if transcribing:
                        memory_buffer.append(text)
                        last_sound_time = time.time()  # Reset silence timer after speech

            # Check for silence timeout while transcribing
            if transcribing and (time.time() - last_sound_time) > 2:
                print("\nSilence detected - stopping transcription and writing to file...")
                transcribing = False

                # Write memory buffer to file
                with open(output_file, "w") as f:
                    f.write("\n".join(memory_buffer))

                print(f"Transcription written to {output_file}\n")
                print(f"Listening for wake word: '{wake_word}'...")

        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

def main():
    try:
        # Create transcription directory if it doesn't exist
        os.makedirs("/home/cisco/Documents/llama/transcription/", exist_ok=True)

        recognizer = setup_vosk()
        audio_stream, audio = setup_audio()

        print("\nStarting transcription service...")
        print("Will automatically stop after 1.5 seconds of silence")
        print("Press Ctrl+C to exit the program\n")

        transcribe_after_wake_word(recognizer, audio_stream)

    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'audio_stream' in locals():
            audio_stream.stop_stream()
            audio_stream.close()
        if 'audio' in locals():
            audio.terminate()

if __name__ == "__main__":
    main()