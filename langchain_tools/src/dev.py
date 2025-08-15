import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from subprocess import Popen

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = time.time()
        self.process = None

    def restart_app(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        print("\n🔄 Restarting application...")
        self.process = Popen([sys.executable, "-m", "src.cli"])

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            current_time = time.time()
            if current_time - self.last_modified > 1:  # Debounce
                self.last_modified = current_time
                self.restart_app()

def main():
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    print("👀 Watching for file changes...")
    event_handler.restart_app()  # Start the app initially

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
        print("\n👋 Stopping file watcher...")
    observer.join()

if __name__ == "__main__":
    main()
