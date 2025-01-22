import torch
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sounddevice as sd
import os
import sys
import re

# Add Kokoro-82M to Python path
kokoro_path = "/home/cisco/Documents/kokoro/Kokoro-82M"
sys.path.append(kokoro_path)

# Now we can import the Kokoro modules
from models import build_model
from kokoro import generate

class TTSHandler(FileSystemEventHandler):
    def __init__(self):
        # Initialize device
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {self.device}")
        
        # Initialize TTS model
        model_path = os.path.join(kokoro_path, "kokoro-v0_19.pth")
        print(f"Loading model from: {model_path}")
        self.model = build_model(model_path, self.device)
        
        # Load default voice
        voice_path = os.path.join(kokoro_path, "voices/af_sky.pt")
        print(f"Loading voice from: {voice_path}")
        self.voicepack = torch.load(voice_path, weights_only=True).to(self.device)
        print("TTS model and voicepack loaded successfully")

    def split_into_sentences(self, text):
        # Split on periods followed by spaces or newlines
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out empty strings
        return [s.strip() for s in sentences if s.strip()]

    def chunk_long_sentence(self, sentence, max_length=100):
        # Split very long sentences on commas or natural break points
        if len(sentence) <= max_length:
            return [sentence]
        
        chunks = []
        # Split on commas, then recombine to keep chunks under max_length
        parts = sentence.split(',')
        current_chunk = ''
        
        for part in parts:
            part = part.strip()
            if len(current_chunk) + len(part) < max_length:
                current_chunk += part + ', '
            else:
                if current_chunk:
                    chunks.append(current_chunk.rstrip(', '))
                current_chunk = part + ', '
        
        if current_chunk:
            chunks.append(current_chunk.rstrip(', '))
            
        return chunks

    def process_response(self, response_path):
        try:
            # Wait briefly to ensure file is fully written
            time.sleep(0.1)
            
            # Read the Llama response
            with open(response_path, 'r') as f:
                text = f.read().strip()
                
            if not text:
                return
                
            print("\nProcessing text for TTS...")
            
            # Split into sentences
            sentences = self.split_into_sentences(text)
            
            # Process each sentence
            for sentence in sentences:
                # Split long sentences into chunks
                chunks = self.chunk_long_sentence(sentence)
                
                for chunk in chunks:
                    print(f"\nGenerating speech for: {chunk}")
                    
                    # Generate audio for this chunk
                    audio, phonemes = generate(
                        self.model,
                        chunk,
                        self.voicepack,
                        lang='a'
                    )
                    
                    # Play audio through speakers
                    sd.play(audio, samplerate=24000)
                    sd.wait()  # Wait until audio finishes playing
                    
                    # Small pause between chunks for natural speech rhythm
                    time.sleep(0.2)
            
            # Save the complete response audio if needed
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            output_dir = "/home/cisco/Documents/llama/audio/"
            os.makedirs(output_dir, exist_ok=True)
            audio_path = os.path.join(output_dir, f"response_{timestamp}.txt")
            
            # Save the text for reference
            with open(audio_path, 'w') as f:
                f.write(text)
                
            print(f"\nProcessing complete. Text saved to: {audio_path}")
            
        except Exception as e:
            print(f"Error processing TTS: {e}")
            print(f"Full error details: {str(e)}")
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('last_response.txt'):
            self.process_response(event.src_path)

def main():
    # Verify paths exist
    if not os.path.exists(kokoro_path):
        print(f"Error: Kokoro directory not found at {kokoro_path}")
        return
        
    model_path = os.path.join(kokoro_path, "kokoro-v0_19.pth")
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return
        
    voice_path = os.path.join(kokoro_path, "voices/af_sky.pt")
    if not os.path.exists(voice_path):
        print(f"Error: Voice file not found at {voice_path}")
        return
    
    # Create necessary directories
    os.makedirs("/home/cisco/Documents/llama/audio/", exist_ok=True)
    
    # Set up file monitoring
    handler = TTSHandler()
    observer = Observer()
    observer.schedule(
        handler, 
        path="/home/cisco/Documents/llama/responses/",
        recursive=False
    )
    
    print("Starting TTS integration...")
    print("Monitoring for Llama responses...")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping TTS integration...")
    observer.join()

if __name__ == "__main__":
    main()