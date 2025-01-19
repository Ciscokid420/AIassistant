import pyaudio

class AudioManager:
    def __init__(self):
        self.audio = None
        self.stream = None
        
    def setup(self):
        """Initialize audio input stream"""
        self.audio = pyaudio.PyAudio()
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8192  # Increased buffer size for better recognition
            )
            self.stream.start_stream()
            print("Audio stream initialized")
            return self.stream
        except Exception as e:
            print(f"Error setting up audio: {e}")
            self.cleanup()
            raise

    def read_audio(self, chunk_size=4096):
        """Read a chunk of audio data"""
        if not self.stream:
            raise RuntimeError("Audio stream not initialized. Call setup() first.")
        return self.stream.read(chunk_size, exception_on_overflow=False)

    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

    @staticmethod
    def is_silent(data, threshold=500):
        """Check if the audio data is silent"""
        # Use a more robust silence detection method
        values = [abs(int.from_bytes(data[i:i+2], 'little', signed=True)) 
                 for i in range(0, len(data), 2)]
        return sum(values) / len(values) < threshold  # Use average instead of max