import subprocess
import sys
import os
import time
import signal
import psutil
from typing import List, Dict
import logging
from datetime import datetime

class VoiceAssistantLauncher:
    def __init__(self):
        self.setup_logging()
        self.processes: Dict[str, subprocess.Popen] = {}
        self.components = {
            'wake_word': 'wake_word.py',
            'llm': 'llama_integration.py',
            'tts': 'tts_integration.py'
        }
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Add status monitoring
        self.last_status = ""

    def setup_logging(self):
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"voice_assistant_{timestamp}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger("VoiceAssistant")

    def monitor_wake_word_status(self):
        """Monitor the wake word status file"""
        status_file = "/home/cisco/Documents/llama/status/wake_word_status.txt"
        try:
            if os.path.exists(status_file):
                with open(status_file, 'r') as f:
                    status = f.read().strip()
                    if status != self.last_status:
                        self.logger.info(f"Wake Word Status: {status}")
                        self.last_status = status
        except Exception as e:
            self.logger.error(f"Error reading wake word status: {str(e)}")

    def start_component(self, name: str, script: str) -> bool:
        try:
            self.logger.info(f"Starting {name} component...")
            
            process = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[name] = process
            self.logger.info(f"{name} component started with PID {process.pid}")
            
            time.sleep(2)
            if process.poll() is not None:
                self.logger.error(f"{name} component failed to start!")
                stdout, stderr = process.communicate()
                self.logger.error(f"stdout: {stdout}")
                self.logger.error(f"stderr: {stderr}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting {name} component: {str(e)}")
            return False

    def monitor_processes(self) -> None:
        while True:
            try:
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        self.logger.warning(f"{name} component has stopped. Restarting...")
                        if self.start_component(name, self.components[name]):
                            self.logger.info(f"{name} component restarted successfully")
                        else:
                            self.logger.error(f"Failed to restart {name} component")
                
                # Monitor wake word status
                self.monitor_wake_word_status()
                
                time.sleep(1)  # Check every second
                
            except KeyboardInterrupt:
                self.cleanup()
                break
            except Exception as e:
                self.logger.error(f"Error in process monitoring: {str(e)}")
                self.cleanup()
                break

    def signal_handler(self, signum, frame):
        self.logger.info(f"Received signal {signum}. Shutting down...")
        self.cleanup()
        sys.exit(0)

    def cleanup(self) -> None:
        self.logger.info("Cleaning up processes...")
        
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    self.logger.info(f"Terminating {name} component (PID: {process.pid})")
                    
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                    
                    for child in children:
                        child.terminate()
                    psutil.wait_procs(children, timeout=3)
                    
                    process.terminate()
                    process.wait(timeout=3)
                    
            except Exception as e:
                self.logger.error(f"Error cleaning up {name} component: {str(e)}")
                try:
                    process.kill()
                except:
                    pass

    def start(self) -> None:
        self.logger.info("Starting Voice Assistant...")
        
        # Create necessary directories
        os.makedirs("/home/cisco/Documents/llama/transcription/", exist_ok=True)
        os.makedirs("/home/cisco/Documents/llama/responses/", exist_ok=True)
        os.makedirs("/home/cisco/Documents/llama/audio/", exist_ok=True)
        os.makedirs("/home/cisco/Documents/llama/status/", exist_ok=True)
        
        startup_sequence = ['wake_word', 'llm', 'tts']
        
        for component in startup_sequence:
            if not self.start_component(component, self.components[component]):
                self.logger.error(f"Failed to start {component}. Aborting startup.")
                self.cleanup()
                sys.exit(1)
            time.sleep(2)
        
        self.logger.info("All components started successfully")
        self.monitor_processes()

def main():
    launcher = VoiceAssistantLauncher()
    launcher.start()

if __name__ == "__main__":
    main()