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
            n_ctx=2048,
            n_batch=1024,
            n_threads=8,
            n_gpu_layers=-1,
            main_gpu=0,
            tensor_split=None,
            seed=-1,
            f16_kv=True,
            use_mmap=True,
            use_mlock=False,
            vocab_only=False,
            verbose=True,
            offload_kqv=True
        )
        
        print("Llama model loaded with GPU acceleration")
        
    def process_transcription(self, transcription_path):
        try:
            time.sleep(0.1)
            
            with open(transcription_path, 'r') as f:
                user_input = f.read().strip()
                
            if not user_input:
                return
                
            prompt = f"""USER: {user_input}
ASSISTANT: """
            
            output = self.llm(
                prompt,
                max_tokens=2000,
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                stop=["USER:"],
                echo=False,
                stream=False,
            )
            
            response = output['choices'][0]['text'].strip()
            print(response)  # Just print the raw response text
            
            with open("/home/cisco/Documents/llama/responses/last_response.txt", "w") as f:
                f.write(response)
                
        except Exception as e:
            print(f"Error processing transcription: {e}")
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('transcription.txt'):
            self.process_transcription(event.src_path)

def main():
    llm_path = "/home/cisco/Documents/llama/ChimeraLlama-3-8B.i1-Q4_0.gguf"
    
    os.makedirs("/home/cisco/Documents/llama/responses/", exist_ok=True)
    
    handler = TranscriptionHandler(llm_path)
    observer = Observer()
    observer.schedule(
        handler, 
        path="/home/cisco/Documents/llama/transcription/",
        recursive=False
    )
    
    print("Starting GPU-accelerated LLM integration...")
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