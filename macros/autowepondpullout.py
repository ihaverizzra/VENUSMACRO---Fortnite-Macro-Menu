import time
from pynput import keyboard
from pynput.keyboard import Listener

class EditSlotBot:
    def __init__(self, edit_button, slot_number):
        self.controller = keyboard.Controller()
        self.edit_button = edit_button
        self.slot_number = slot_number
        self.edit_held = False
        
        print(f"\nBot configured:")
        print(f"Edit button: '{edit_button}'")
        print(f"Slot number: '{slot_number}'")
        print(f"\nHold '{edit_button}' and release to trigger slot '{slot_number}'!")
        print("Press Ctrl+C to exit")
    
    def click_slot(self):
        time.sleep(0.1)
        self.controller.press(self.slot_number)
        self.controller.release(self.slot_number)
        print(f"Clicked slot '{self.slot_number}'!")
    
    def on_press(self, key):
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key).replace('Key.', '')
        
        if key_char == self.edit_button and not self.edit_held:
            self.edit_held = True
            print(f"Edit button '{self.edit_button}' held - waiting for release...")
    
    def on_release(self, key):
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key).replace('Key.', '')
        
        if key_char == self.edit_button and self.edit_held:
            self.edit_held = False
            print(f"Edit button '{self.edit_button}' released!")
            self.click_slot()
        
        if key == keyboard.Key.ctrl_l:
            return False
    
    def start(self):
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                print("\nExiting...")

def main():
    print("This will click your slot number with a delay when you release your edit button.\n")
    
    edit_button = input("Enter your edit button (for example 'g'): ").strip().lower()
    slot_number = input("Enter your slot number (for example '2'): ").strip()
    
    if not edit_button or not slot_number:
        print("Error: Both edit button and slot number must be specified!")
        return
    
    if len(edit_button) > 1:
        print("Error: Edit button must be a single character (a-z, 0-9)")
        return
    
    if len(slot_number) > 1 or not slot_number.isdigit():
        print("Error: Slot number must be a single digit (0-9)")
        return
    
    try:
        bot = EditSlotBot(edit_button, slot_number)
        bot.start()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to install pynput: pip install pynput")

if __name__ == "__main__":
    main()