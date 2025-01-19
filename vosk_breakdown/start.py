from audio_manager import AudioManager
from voice_recognizer import VoiceRecognizer
from transcription_manager import TranscriptionManager
from wake_word_detector import WakeWordDetector

class TranscriptionService:
    def __init__(self):
        self.audio_manager = AudioManager()
        self.voice_recognizer = VoiceRecognizer()
        self.transcription_manager = TranscriptionManager()
        self.wake_word_detector = WakeWordDetector()
        
    def setup(self):
        """Initialize all components"""
        try:
            # Initialize all components in the correct order
            self.transcription_manager.setup()
            self.recognizer = self.voice_recognizer.setup()  # Store the recognizer instance
            self.stream = self.audio_manager.setup()  # Store the audio stream
        except Exception as e:
            print(f"Error during setup: {e}")
            self.cleanup()
            raise
            
    def run(self):
        """Main service loop"""
        print("\nStarting transcription service...")
        print("Will automatically stop after 2 seconds of silence")
        print("Press Ctrl+C to exit the program\n")
        print(f"Listening for wake word: '{self.wake_word_detector.get_wake_word()}'...")
        
        try:
            while True:
                # Read audio data
                audio_data = self.audio_manager.read_audio()
                
                # Update silence detection
                if not self.audio_manager.is_silent(audio_data):
                    self.transcription_manager.update_last_sound_time()
                
                # Process audio through voice recognition
                text = self.voice_recognizer.process_audio(audio_data)
                if not text:  # If no text was returned, continue to next iteration
                    continue
                
                if text:
                    print("Heard:", text)
                    
                    # Check for wake word if not already transcribing
                    if not self.transcription_manager.transcribing:
                        if self.wake_word_detector.detect(text):
                            self.transcription_manager.start_transcription()
                            continue
                    
                    # Add text to transcription if we're currently transcribing
                    self.transcription_manager.add_text(text)
                
                # Check for silence timeout
                if self.transcription_manager.check_silence_timeout():
                    self.transcription_manager.stop_transcription()
                    print(f"Listening for wake word: '{self.wake_word_detector.get_wake_word()}'...")
                    
        except KeyboardInterrupt:
            print("\nStopping service...")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up all resources"""
        self.audio_manager.cleanup()

def main():
    service = TranscriptionService()
    try:
        service.setup()
        service.run()
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()