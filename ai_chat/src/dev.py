"""Development server with auto-reload for the AI Chat CLI."""

import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class ChangeHandler(FileSystemEventHandler):
    """Handle file system events and restart the CLI."""
    
    def __init__(self):
        self.process = None
        self.restart_program()
    
    def restart_program(self):
        """Kill the existing process and start a new one."""
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        # Clear the screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Start the CLI in a new process
        self.process = subprocess.Popen(
            ["poetry", "run", "python", "-m", "src.cli"],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
    
    def on_modified(self, event):
        """Called when a file is modified."""
        if event.src_path.endswith('.py'):
            print("\n🔄 Reloading due to changes...")
            self.restart_program()


def main():
    """Run the development server with auto-reload."""
    # Set up file system observer
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path='src', recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join()


if __name__ == "__main__":
    main()