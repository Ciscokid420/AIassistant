from collections import deque
import time
import os

class TranscriptionManager:
    def __init__(self, output_dir="/home/cisco/Documents/llama/transcription/"):
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, "transcription.txt")
        self.memory_buffer = deque()
        self.transcribing = False
        self.last_sound_time = time.time()
        self.silence_timeout = 2.0  # Configurable silence timeout
        
    def setup(self):
        """Create necessary directories"""
        os.makedirs(self.output_dir, exist_ok=True)
        
    def start_transcription(self):
        """Start a new transcription session"""
        self.transcribing = True
        self.memory_buffer.clear()
        self.last_sound_time = time.time()
        print(f"\nStarting transcription to {self.output_file}\n")
        
    def stop_transcription(self):
        """Stop transcription and save to file"""
        if self.transcribing:
            self.transcribing = False
            if self.memory_buffer:  # Only save if there's something to save
                self._save_transcription()
            
    def update_last_sound_time(self):
        """Update the last sound timestamp"""
        self.last_sound_time = time.time()
        
    def add_text(self, text):
        """Add text to the transcription buffer"""
        if text and self.transcribing:
            # Only add text if it's not a duplicate of the last entry
            if not self.memory_buffer or text != self.memory_buffer[-1]:
                self.memory_buffer.append(text)
                self.update_last_sound_time()
            
    def check_silence_timeout(self):
        """Check if silence timeout has been reached"""
        return (self.transcribing and 
                (time.time() - self.last_sound_time) > self.silence_timeout)
        
    def _save_transcription(self):
        """Save the transcription buffer to file"""
        print("\nSaving transcription to file...")
        with open(self.output_file, "w") as f:
            f.write("\n".join(self.memory_buffer))
        print(f"Transcription written to {self.output_file}\n")