import time
import threading
from pynput import keyboard
from pynput.keyboard import Listener

class SimpleKeyBot:
    def __init__(self, edit_key, secondary_key, toggle_key):
        self.controller = keyboard.Controller()
        self.edit_key = edit_key
        self.secondary_key = secondary_key
        self.toggle_key = toggle_key
        self.is_running = False
        self.thread = None
        
        print(f"Edit key: '{edit_key}'")
        print(f"Secondary key: '{secondary_key}'")
        print(f"Toggle key: '{toggle_key}'")
        print(f"\nHold '{toggle_key}' to start")
        print("Press Ctrl+C to exit")
    
    def execute_sequence(self):
        self.controller.press(self.edit_key)
        time.sleep(0.01)
        self.controller.release(self.edit_key)
        
        self.controller.press(self.secondary_key)
        time.sleep(0.01)
        self.controller.release(self.secondary_key)
    
    def sequence_loop(self):
        while self.is_running:
            self.execute_sequence()
            time.sleep(0.001)  # Small delay between cycles
    
    def on_press(self, key):
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key).replace('Key.', '')
        
        if key_char == self.toggle_key and not self.is_running:
            print(f"Starting sequence! (Holding '{self.toggle_key}')")
            self.is_running = True
            self.thread = threading.Thread(target=self.sequence_loop)
            self.thread.daemon = True
            self.thread.start()
    
    def on_release(self, key):
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key).replace('Key.', '')
        
        if key_char == self.toggle_key and self.is_running:
            print(f"Stopping sequence! (Released '{self.toggle_key}')")
            self.is_running = False
        
        if key == keyboard.Key.ctrl_l:
            return False
    
    def start(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\nExiting...")
                self.is_running = False

def main():
    
    edit_key = input("Enter your edit key bind (for example 'g'): ").strip().lower()
    secondary_key = input("Enter your secondary select edit bind (for example 'o'): ").strip().lower()
    toggle_key = input("Enter your toggle button (for example 't'): ").strip().lower()
    
    if not edit_key or not secondary_key or not toggle_key:
        print("Error: All keys must be specified!")
        return
    
    if len(edit_key) > 1 or len(secondary_key) > 1 or len(toggle_key) > 1:
        print("Error: Please use single character keys (a-z, 0-9)")
        return
    
    try:
        bot = SimpleKeyBot(edit_key, secondary_key, toggle_key)
        bot.start()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to install pynput: pip install pynput")

if __name__ == "__main__":
    main()