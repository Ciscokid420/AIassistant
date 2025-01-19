from vosk import Model, KaldiRecognizer
import json

class VoiceRecognizer:
    def __init__(self, model_path="/home/cisco/Documents/Vosk/vosk-model-small-en-us-0.15"):
        self.model_path = model_path
        self.recognizer = None
        self.last_text = ""  # Track last processed text to avoid duplicates
        
    def setup(self):
        """Initialize the Vosk model and recognizer"""
        try:
            model = Model(self.model_path)
            print("Model loaded successfully")
            self.recognizer = KaldiRecognizer(model, 16000)
            self.recognizer.SetWords(True)
            return self.recognizer
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def process_audio(self, audio_data):
        """Process audio data and return recognized text"""
        if not self.recognizer:
            raise RuntimeError("Recognizer not initialized. Call setup() first.")
            
        # Only process complete utterances, ignore partials to avoid duplicates
        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "").strip()
            
            # Only return text if it's different from the last processed text
            if text and text != self.last_text:
                self.last_text = text
                return text
            
        return ""  # Return empty string if no new complete utterance