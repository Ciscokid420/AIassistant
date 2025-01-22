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
            frames_per_buffer=5000
        )
        stream.start_stream()
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
    memory_buffer = deque()
    status_file = "/home/cisco/Documents/llama/status/wake_word_status.txt"
    
    # Create status directory if it doesn't exist
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
    
    # Initial status
    with open(status_file, "w") as f:
        f.write("Waiting for Hey Dexter")
    
    print("Waiting for Hey Dexter")

    while True:
        try:
            data = audio_stream.read(4096, exception_on_overflow=False)

            if not is_silent(data):
                last_sound_time = time.time()

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                if text:
                    if not transcribing and wake_word.lower() in text.lower():
                        transcribing = True
                        status = "Wake word detected - Listening..."
                        print(status)
                        with open(status_file, "w") as f:
                            f.write(status)
                        last_sound_time = time.time()
                        memory_buffer.clear()
                        continue

                    if transcribing:
                        memory_buffer.append(text)
                        last_sound_time = time.time()

            if transcribing and (time.time() - last_sound_time) > 2:
                transcribing = False
                
                with open(output_file, "w") as f:
                    f.write("\n".join(memory_buffer))
                
                status = "Waiting for Hey Dexter"
                print(status)
                with open(status_file, "w") as f:
                    f.write(status)

        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

def main():
    try:
        os.makedirs("/home/cisco/Documents/llama/transcription/", exist_ok=True)
        os.makedirs("/home/cisco/Documents/llama/status/", exist_ok=True)

        recognizer = setup_vosk()
        audio_stream, audio = setup_audio()

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