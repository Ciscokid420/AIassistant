class WakeWordDetector:
    def __init__(self, wake_word="hey dexter"):
        self.wake_word = wake_word.lower()
        
    def detect(self, text):
        """Check if the wake word is present in the text"""
        return self.wake_word in text.lower()
        
    def get_wake_word(self):
        """Return the current wake word"""
        return self.wake_word