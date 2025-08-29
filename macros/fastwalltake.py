import time
from pynput import keyboard, mouse
from pynput.keyboard import Listener

class WallSequenceBot:
    def __init__(self, wall_button, trigger_key):
        self.keyboard_controller = keyboard.Controller()
        self.mouse_controller = mouse.Controller()
        self.wall_button = wall_button
        self.trigger_key = trigger_key
        self.running_sequence = False
        
        print(f"\nBot configured:")
        print(f"Wall button: '{wall_button}'")
        print(f"Trigger key: '{trigger_key}'")
        print(f"\nPress '{trigger_key}' to execute the wall sequence!")
        print("Press Ctrl+C to exit")
    
    def execute_sequence(self):
        if self.running_sequence:
            return
        
        self.running_sequence = True
        print("Executing wall sequence...")
        
        self.mouse_controller.press(mouse.Button.left)
        time.sleep(0.20)
        self.mouse_controller.release(mouse.Button.left)
        
        self.keyboard_controller.press(self.wall_button)
        time.sleep(0.05)
        self.keyboard_controller.release(self.wall_button)
        
        self.mouse_controller.press(mouse.Button.left)
        time.sleep(0.10)
        self.mouse_controller.release(mouse.Button.left)
        
        print("Sequence completed!")
        self.running_sequence = False
    
    def on_press(self, key):
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key).replace('Key.', '')
        
        if key_char == self.trigger_key:
            self.execute_sequence()
    
    def on_release(self, key):
        if key == keyboard.Key.ctrl_l:
            return False
    
    def start(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\nExiting...")

def main():
    print("This executes a specific sequence for wall placement.\n")
    
    wall_button = input("Enter your wall placement button (for example 'p'): ").strip().lower()
    trigger_key = input("Enter your trigger key (for example 't'): ").strip().lower()
    
    if not wall_button or not trigger_key:
        print("Error: Both wall button and trigger key must be specified!")
        return
    
    if len(wall_button) > 1 or len(trigger_key) > 1:
        print("Error: Keys must be single characters (a-z, 0-9)")
        return
    
    try:
        bot = WallSequenceBot(wall_button, trigger_key)
        bot.start()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to install pynput: pip install pynput")

if __name__ == "__main__":
    main()