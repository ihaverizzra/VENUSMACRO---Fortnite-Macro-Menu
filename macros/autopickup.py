import time
import threading
from pynput import keyboard, mouse
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener

class PickupSpamBot:
    def __init__(self, pickup_key, trigger_key):
        self.keyboard_controller = keyboard.Controller()
        self.pickup_key = pickup_key
        self.trigger_key = trigger_key
        self.is_spamming = False
        self.spam_thread = None
        
        print(f"\nBot configured:")
        print(f"Pickup key: '{pickup_key}'")
        print(f"Trigger key: '{trigger_key}'")
        print(f"\nHold '{trigger_key}' to spam '{pickup_key}'!")
        print("Press Ctrl+C to exit")
    
    def spam_pickup(self):
        while self.is_spamming:
            self.keyboard_controller.press(self.pickup_key)
            self.keyboard_controller.release(self.pickup_key)
            time.sleep(0.01)
    
    def start_spamming(self):
        if not self.is_spamming:
            self.is_spamming = True
            self.spam_thread = threading.Thread(target=self.spam_pickup)
            self.spam_thread.daemon = True
            self.spam_thread.start()
            print(f"Started spamming '{self.pickup_key}'!")
    
    def stop_spamming(self):
        if self.is_spamming:
            self.is_spamming = False
            print(f"Stopped spamming '{self.pickup_key}'!")
    
    def on_mouse_press(self, x, y, button):
        if str(button) == self.trigger_key:
            self.start_spamming()
    
    def on_mouse_release(self, x, y, button):
        if str(button) == self.trigger_key:
            self.stop_spamming()
    
    def on_key_press(self, key):
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key)
        
        if key_char == self.trigger_key:
            self.start_spamming()
    
    def on_key_release(self, key):
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key)
            if key == keyboard.Key.ctrl_l:
                return False
        
        if key_char == self.trigger_key:
            self.stop_spamming()
    
    def start(self):
        mouse_listener = MouseListener(
            on_click=self.on_mouse_press,
        )
        keyboard_listener = KeyboardListener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        
        def on_mouse_click(x, y, button, pressed):
            if str(button) == self.trigger_key:
                if pressed:
                    self.start_spamming()
                else:
                    self.stop_spamming()
        
        mouse_listener = MouseListener(on_click=on_mouse_click)
        mouse_listener.start()
        keyboard_listener.start()
        
        try:
            keyboard_listener.join()
        except KeyboardInterrupt:
            print("\nExiting...")
            self.is_spamming = False

def main():
    print("This will spam your pickup key while holding your trigger key.\n")
    
    pickup_key = input("Enter your pickup key (for example 'e'): ").strip().lower()
    
    print("\nFor trigger key, you can use:")
    print("- Keyboard keys: letters (a-z), numbers (0-9)")
    print("- Mouse buttons: Button.x1 (side button), Button.x2 (side button)")
    print("- Examples: 't', 'f', '5', 'Button.x1', 'Button.x2'")
    
    trigger_key = input("Enter your trigger key: ").strip()
    
    if not pickup_key or not trigger_key:
        print("Error: Both pickup key and trigger key must be specified!")
        return
    
    if len(pickup_key) > 1 and not pickup_key.isdigit():
        print("Error: Pickup key must be a single character (a-z, 0-9)")
        return
    
    try:
        bot = PickupSpamBot(pickup_key, trigger_key)
        bot.start()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to install pynput: pip install pynput")

if __name__ == "__main__":
    main()