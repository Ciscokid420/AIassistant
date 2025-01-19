import subprocess
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from llama_cpp import Llama

class TranscriptionHandler(FileSystemEventHandler):
    def __init__(self, llm_path):
        self.llm = Llama(
            model_path=llm_path,
            n_ctx=2048,  # Adjust context window as needed
            n_threads=4   # Adjust based on your CPU
        )
        
    def process_transcription(self, transcription_path):
        try:
            # Wait briefly to ensure file is fully written
            time.sleep(0.1)
            
            with open(transcription_path, 'r') as f:
                user_input = f.read().strip()
                
            if not user_input:
                return
                
            print("\nProcessing transcription:", user_input)
            
            # Create a conversation prompt
            prompt = f"""USER: {user_input}
ASSISTANT: """
            
            # Generate response
            output = self.llm(
                prompt,
                max_tokens=500,
                temperature=0.7,
                stop=["USER:"],  # Stop at next user input
                echo=False
            )
            
            response = output['choices'][0]['text'].strip()
            print("\nLLM Response:", response)
            
            # Optionally save response to a file
            with open("/home/cisco/Documents/llama/responses/last_response.txt", "w") as f:
                f.write(response)
                
        except Exception as e:
            print(f"Error processing transcription: {e}")
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('transcription.txt'):
            self.process_transcription(event.src_path)

def main():
    # Path to your GGUF model file
    llm_path = "/home/cisco/.lmstudio/models/LWDCLS/DarkIdol-Llama-3.1-8B-Instruct-1.2-Uncensored-GGUF-IQ-Imatrix-Request/DarkIdol-Llama-3.1-8B-Instruct-1.2-Uncensored-Q4_K_S-imat.gguf"  # Update this path
    
    # Create response directory
    os.makedirs("/home/cisco/Documents/llama/responses/", exist_ok=True)
    
    # Set up file monitoring
    handler = TranscriptionHandler(llm_path)
    observer = Observer()
    observer.schedule(
        handler, 
        path="/home/cisco/Documents/llama/transcription/",
        recursive=False
    )
    
    print("Starting LLM integration...")
    print("Monitoring for transcriptions...")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping LLM integration...")
    observer.join()

if __name__ == "__main__":
    main()