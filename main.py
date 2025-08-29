import sys
import time
import threading
import json
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from pynput import keyboard, mouse
from pynput.keyboard import Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener


class KeyCaptureDialog(QDialog):
    """Dialog for capturing key presses"""
    
    key_captured = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Press a key...")
        self.setModal(True)
        self.setFixedSize(300, 150)
        self.captured_key = None
        self.listener = None
        self.setup_ui()
        QTimer.singleShot(100, self.setup_listener)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.label = QLabel("Press any key to bind...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 16px; color: #ffffff; margin: 20px;")
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        
        layout.addWidget(self.label)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)
        
        self.key_captured.connect(self.on_key_captured)
    
    def setup_listener(self):
        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char:
                    key_str = key.char
                else:
                    key_str = str(key).replace('Key.', '').lower()
                
                self.key_captured.emit(key_str)
                return False
                
            except Exception as e:
                print(f"Key capture error: {e}")
                return True
        
        try:
            self.listener = KeyboardListener(on_press=on_press)
            self.listener.start()
        except Exception as e:
            print(f"Failed to start listener: {e}")
            self.reject()
    
    @Slot(str)
    def on_key_captured(self, key_str):
        self.captured_key = key_str
        self.label.setText(f"Captured: {key_str}")
        QTimer.singleShot(200, self.accept)
    
    def reject(self):
        self.cleanup_listener()
        super().reject()
    
    def accept(self):
        self.cleanup_listener()
        super().accept()
    
    def cleanup_listener(self):
        if self.listener and self.listener.running:
            try:
                self.listener.stop()
            except:
                pass
            self.listener = None
    
    def closeEvent(self, event):
        self.cleanup_listener()
        event.accept()


class ScriptBot(QObject):
    status_changed = Signal(str, str)
    
    def __init__(self):
        super().__init__()
        self.keyboard_controller = keyboard.Controller()
        self.mouse_controller = mouse.Controller()
        self.listeners = []
        self.active_scripts = {}
        self.running_threads = {}
        self._thread_stop_events = {}
        
    def stop_all_scripts(self):
        for script_name in list(self.active_scripts.keys()):
            self.stop_script(script_name)
        
        for listener in self.listeners[:]:
            try:
                if hasattr(listener, 'running') and listener.running:
                    listener.stop()
                self.listeners.remove(listener)
            except:
                pass
        
        for event in self._thread_stop_events.values():
            event.set()
        self._thread_stop_events.clear()
        self.running_threads.clear()
    
    def stop_script(self, script_name):
        if script_name in self.active_scripts:
            self.active_scripts[script_name] = False
            
        if script_name in self._thread_stop_events:
            self._thread_stop_events[script_name].set()
            
        self.status_changed.emit(script_name, "Stopped")
    
    def _normalize_key(self, key_input):
        if not key_input:
            return ""
        
        key_str = str(key_input).lower().strip()
        key_mappings = {
            'space': 'space',
            'enter': 'enter',
            'tab': 'tab',
            'shift': 'shift',
            'ctrl': 'ctrl',
            'alt': 'alt',
            'escape': 'esc',
            'backspace': 'backspace',
            'delete': 'delete'
        }
        
        return key_mappings.get(key_str, key_str)
    
    def start_spam_macro(self, edit_key, secondary_key, toggle_key):
        self.stop_all_scripts()
        self.active_scripts['spam_macro'] = False
        stop_event = threading.Event()
        self._thread_stop_events['spam_macro'] = stop_event
        
        edit_key = self._normalize_key(edit_key)
        secondary_key = self._normalize_key(secondary_key)
        toggle_key = self._normalize_key(toggle_key)
        
        def execute_sequence():
            try:
                if edit_key == 'space':
                    self.keyboard_controller.press(keyboard.Key.space)
                    time.sleep(0.01)
                    self.keyboard_controller.release(keyboard.Key.space)
                else:
                    self.keyboard_controller.press(edit_key)
                    time.sleep(0.01)
                    self.keyboard_controller.release(edit_key)
                
                if secondary_key == 'space':
                    self.keyboard_controller.press(keyboard.Key.space)
                    time.sleep(0.01)
                    self.keyboard_controller.release(keyboard.Key.space)
                else:
                    self.keyboard_controller.press(secondary_key)
                    time.sleep(0.01)
                    self.keyboard_controller.release(secondary_key)
            except Exception as e:
                print(f"Sequence execution error: {e}")
        
        def sequence_loop():
            while self.active_scripts.get('spam_macro', False) and not stop_event.is_set():
                execute_sequence()
                time.sleep(0.001)
        
        def on_press(key):
            try:
                key_char = getattr(key, 'char', None) or str(key).replace('Key.', '').lower()
                key_char = self._normalize_key(key_char)
                
                if key_char == toggle_key and not self.active_scripts.get('spam_macro', False):
                    self.active_scripts['spam_macro'] = True
                    self.status_changed.emit('spam_macro', f'Running (Hold {toggle_key})')
                    thread = threading.Thread(target=sequence_loop, daemon=True)
                    thread.start()
                    self.running_threads['spam_macro'] = thread
            except Exception as e:
                print(f"Key press error: {e}")
        
        def on_release(key):
            try:
                key_char = getattr(key, 'char', None) or str(key).replace('Key.', '').lower()
                key_char = self._normalize_key(key_char)
                
                if key_char == toggle_key and self.active_scripts.get('spam_macro', False):
                    self.active_scripts['spam_macro'] = False
                    self.status_changed.emit('spam_macro', 'Ready')
            except Exception as e:
                print(f"Key release error: {e}")
        
        try:
            listener = KeyboardListener(on_press=on_press, on_release=on_release)
            listener.start()
            self.listeners.append(listener)
            self.status_changed.emit('spam_macro', 'Ready')
        except Exception as e:
            print(f"Listener start error: {e}")
            self.status_changed.emit('spam_macro', 'Error')
    
    def start_auto_pullout(self, edit_key, slot_number):
        self.stop_all_scripts()
        self.active_scripts['auto_pullout'] = True
        edit_held = False
        
        edit_key = self._normalize_key(edit_key)
        slot_number = self._normalize_key(slot_number)
        
        def click_slot():
            try:
                time.sleep(0.1)
                self.keyboard_controller.press(slot_number)
                time.sleep(0.01)
                self.keyboard_controller.release(slot_number)
            except Exception as e:
                print(f"Slot click error: {e}")
        
        def on_press(key):
            nonlocal edit_held
            try:
                key_char = getattr(key, 'char', None) or str(key).replace('Key.', '').lower()
                key_char = self._normalize_key(key_char)
                
                if key_char == edit_key and not edit_held:
                    edit_held = True
                    self.status_changed.emit('auto_pullout', 'Edit held - waiting for release')
            except Exception as e:
                print(f"Auto pullout press error: {e}")
        
        def on_release(key):
            nonlocal edit_held
            try:
                key_char = getattr(key, 'char', None) or str(key).replace('Key.', '').lower()
                key_char = self._normalize_key(key_char)
                
                if key_char == edit_key and edit_held:
                    edit_held = False
                    threading.Thread(target=click_slot, daemon=True).start()
                    self.status_changed.emit('auto_pullout', 'Ready')
            except Exception as e:
                print(f"Auto pullout release error: {e}")
        
        try:
            listener = KeyboardListener(on_press=on_press, on_release=on_release)
            listener.start()
            self.listeners.append(listener)
            self.status_changed.emit('auto_pullout', 'Ready')
        except Exception as e:
            print(f"Auto pullout listener error: {e}")
            self.status_changed.emit('auto_pullout', 'Error')
    
    def start_auto_pickup(self, pickup_key, trigger_key):
        self.stop_all_scripts()
        self.active_scripts['auto_pickup'] = False
        stop_event = threading.Event()
        self._thread_stop_events['auto_pickup'] = stop_event
        
        pickup_key = self._normalize_key(pickup_key)
        trigger_key = self._normalize_key(trigger_key)
        
        def spam_pickup():
            while self.active_scripts.get('auto_pickup', False) and not stop_event.is_set():
                try:
                    self.keyboard_controller.press(pickup_key)
                    time.sleep(0.005)
                    self.keyboard_controller.release(pickup_key)
                    time.sleep(0.01)
                except Exception as e:
                    print(f"Pickup spam error: {e}")
                    break
        
        def start_spamming():
            if not self.active_scripts.get('auto_pickup', False):
                self.active_scripts['auto_pickup'] = True
                self.status_changed.emit('auto_pickup', f'Spamming {pickup_key}')
                thread = threading.Thread(target=spam_pickup, daemon=True)
                thread.start()
                self.running_threads['auto_pickup'] = thread
        
        def stop_spamming():
            if self.active_scripts.get('auto_pickup', False):
                self.active_scripts['auto_pickup'] = False
                self.status_changed.emit('auto_pickup', 'Ready')
        
        def on_key_press(key):
            try:
                key_char = getattr(key, 'char', None) or str(key).replace('Key.', '').lower()
                key_char = self._normalize_key(key_char)
                
                if key_char == trigger_key:
                    start_spamming()
            except Exception as e:
                print(f"Pickup key press error: {e}")
        
        def on_key_release(key):
            try:
                key_char = getattr(key, 'char', None) or str(key).replace('Key.', '').lower()
                key_char = self._normalize_key(key_char)
                
                if key_char == trigger_key:
                    stop_spamming()
            except Exception as e:
                print(f"Pickup key release error: {e}")
        
        def on_mouse_click(x, y, button, pressed):
            try:
                button_str = str(button).lower().replace('button.', '')
                if button_str == trigger_key:
                    if pressed:
                        start_spamming()
                    else:
                        stop_spamming()
            except Exception as e:
                print(f"Mouse click error: {e}")
        
        try:
            keyboard_listener = KeyboardListener(on_press=on_key_press, on_release=on_key_release)
            mouse_listener = MouseListener(on_click=on_mouse_click)
            
            keyboard_listener.start()
            mouse_listener.start()
            self.listeners.extend([keyboard_listener, mouse_listener])
            self.status_changed.emit('auto_pickup', 'Ready')
        except Exception as e:
            print(f"Auto pickup listener error: {e}")
            self.status_changed.emit('auto_pickup', 'Error')
    
    def start_wall_take(self, wall_button, trigger_key):
        self.stop_all_scripts()
        self.active_scripts['wall_take'] = True
        running_sequence = False
        
        wall_button = self._normalize_key(wall_button)
        trigger_key = self._normalize_key(trigger_key)
        
        def execute_sequence():
            nonlocal running_sequence
            if running_sequence:
                return
            
            running_sequence = True
            self.status_changed.emit('wall_take', 'Executing sequence...')
            
            try:
                self.mouse_controller.press(mouse.Button.left)
                time.sleep(0.20)
                self.mouse_controller.release(mouse.Button.left)
                
                self.keyboard_controller.press(wall_button)
                time.sleep(0.05)
                self.keyboard_controller.release(wall_button)
                
                self.mouse_controller.press(mouse.Button.left)
                time.sleep(0.10)
                self.mouse_controller.release(mouse.Button.left)
                
            except Exception as e:
                print(f"Wall sequence error: {e}")
            finally:
                running_sequence = False
                self.status_changed.emit('wall_take', 'Ready')
        
        def on_press(key):
            try:
                key_char = getattr(key, 'char', None) or str(key).replace('Key.', '').lower()
                key_char = self._normalize_key(key_char)
                
                if key_char == trigger_key:
                    threading.Thread(target=execute_sequence, daemon=True).start()
            except Exception as e:
                print(f"Wall take press error: {e}")
        
        try:
            listener = KeyboardListener(on_press=on_press, on_release=lambda key: None)
            listener.start()
            self.listeners.append(listener)
            self.status_changed.emit('wall_take', 'Ready')
        except Exception as e:
            print(f"Wall take listener error: {e}")
            self.status_changed.emit('wall_take', 'Error')


class ClickableLineEdit(QLineEdit):
    clicked = Signal()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class FortniteScriptGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Keybind Manager")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(900, 600)
        
        self.script_bot = ScriptBot()
        self.script_bot.status_changed.connect(self.update_script_status)
        
        self.keybinds = {
            'edit_key': 'g',
            'secondary_edit_key': 'v', 
            'toggle_button': 't',
            'weapon_slot': '2',
            'pickup_key': 'e',
            'pickup_trigger': 'f',
            'wall_button': 'p',
            'wall_trigger': 'r'
        }
        
        self.script_states = {
            'spam_macro': False,
            'auto_pullout': False, 
            'auto_pickup': False,
            'wall_take': False
        }
        
        self.load_settings()
        self.setup_style()
        self.setup_ui()
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.save_settings)
        self.auto_save_timer.start(5000)
    
    def setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1a1a1a, stop:1 #2d2d2d);
                color: #ffffff;
            }
            
            QListWidget {
                background-color: rgba(45, 45, 45, 0.9);
                border: none;
                border-right: 2px solid #007acc;
                padding: 10px 5px;
                font-size: 14px;
                font-weight: bold;
            }
            
            QListWidget::item {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 15px 20px;
                margin: 3px 0;
                color: #cccccc;
            }
            
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            
            QListWidget::item:hover:!selected {
                background-color: rgba(0, 122, 204, 0.3);
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007acc, stop:1 #005a9e);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0084cc, stop:1 #0066aa);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #005a9e, stop:1 #004578);
            }
            
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            
            QLineEdit {
                background-color: rgba(61, 61, 61, 0.8);
                border: 2px solid #555;
                color: white;
                padding: 10px 12px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                min-height: 20px;
            }
            
            QLineEdit:focus {
                border-color: #007acc;
                background-color: rgba(61, 61, 61, 1.0);
            }
            
            QLineEdit:hover {
                border-color: #0084cc;
            }
            
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            
            QCheckBox {
                color: white;
                font-size: 14px;
                font-weight: bold;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
                border: 2px solid #555;
                border-radius: 4px;
                background-color: rgba(61, 61, 61, 0.8);
            }
            
            QCheckBox::indicator:hover {
                border-color: #007acc;
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #007acc, stop:1 #005a9e);
                border-color: #007acc;
            }
            
            QCheckBox::indicator:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0084cc, stop:1 #0066aa);
            }
            
            QScrollArea {
                background: transparent;
                border: none;
            }
            
            QScrollBar:vertical {
                background-color: rgba(45, 45, 45, 0.5);
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #007acc;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #0084cc;
            }
            
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(45, 45, 45, 0.9), 
                    stop:1 rgba(35, 35, 35, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                margin: 5px;
            }
            
            QMessageBox {
                background-color: #2d2d2d;
                color: white;
            }
            
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
        """)
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        sidebar = QListWidget()
        sidebar.setMaximumWidth(220)
        sidebar.setMinimumWidth(220)
        sidebar.addItems(["Scripts", "Keybinds", "Status"])
        sidebar.setCurrentRow(0)
        sidebar.currentItemChanged.connect(self.sidebar_changed)
        
        self.content_stack = QStackedWidget()
        
        self.setup_scripts_page()
        self.setup_keybinds_page()
        self.setup_status_page()
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_stack)
    
    def setup_scripts_page(self):
        scripts_page = QWidget()
        layout = QVBoxLayout(scripts_page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        header_layout = QHBoxLayout()
        title = QLabel("Script Manager")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #007acc; margin-bottom: 10px;")
        
        status_indicator = QLabel("Ready")
        status_indicator.setStyleSheet("font-size: 16px; color: #28a745; font-weight: bold;")
        self.status_indicator = status_indicator
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(status_indicator)
        layout.addLayout(header_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        self.script_cards = {}
        scripts = [
            ('spam_macro', 'Fast Edit Spam', 
             'Rapidly alternates between edit and secondary edit keys while toggle key is held'),
            ('auto_pullout', 'Auto Pull Out Weapon', 
             'Automatically switches to weapon slot when edit key is released'),
            ('auto_pickup', 'Auto Pickup', 
             'Continuously spam pickup key while holding the trigger key'),
            ('wall_take', 'Fast Wall Take', 
             'Execute optimized wall replacement sequence on trigger key press')
        ]
        
        for script_id, name, description in scripts:
            card = self.create_script_card(script_id, name, description)
            self.script_cards[script_id] = card
            scroll_layout.addWidget(card['frame'])
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        stop_all_btn = QPushButton("Stop All")
        stop_all_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
                font-size: 14px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e45565, stop:1 #d02535);
            }
        """)
        stop_all_btn.clicked.connect(self.stop_all_scripts)
        
        self.apply_button = QPushButton("Apply & Save")
        self.apply_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #218838);
                font-size: 16px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34ce57, stop:1 #28a745);
            }
        """)
        self.apply_button.clicked.connect(self.apply_scripts)
        
        button_layout.addWidget(stop_all_btn)
        button_layout.addWidget(self.apply_button)
        layout.addLayout(button_layout)
        
        self.content_stack.addWidget(scripts_page)
    
    def create_script_card(self, script_id, name, description):
        frame = QFrame()
        frame.setMinimumHeight(120)
        frame.setStyleSheet("QFrame { padding: 20px; }")
        
        layout = QHBoxLayout(frame)
        layout.setSpacing(20)
        
        checkbox = QCheckBox()
        checkbox.setChecked(self.script_states[script_id])
        checkbox.stateChanged.connect(lambda state, sid=script_id: self.toggle_script(sid, state == 2))
        
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        
        title_label = QLabel(name)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #cccccc; font-size: 13px; line-height: 1.4;")
        desc_label.setWordWrap(True)
        
        status_label = QLabel("Inactive")
        status_label.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 12px; margin-top: 5px;")
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(desc_label)
        content_layout.addWidget(status_label)
        content_layout.addStretch()
        
        layout.addWidget(checkbox)
        layout.addLayout(content_layout)
        layout.addStretch()
        
        return {
            'frame': frame,
            'checkbox': checkbox,
            'status': status_label
        }
    
    def setup_keybinds_page(self):
        keybinds_page = QWidget()
        layout = QVBoxLayout(keybinds_page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("Keybind Configuration")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #007acc; margin-bottom: 10px;")
        layout.addWidget(title)
        
        instructions = QLabel("Click on any keybind field to capture a new key press, or type manually.")
        instructions.setStyleSheet("color: #cccccc; font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(instructions)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        self.keybind_inputs = {}
        keybind_groups = [
            ("Edit Controls", [
                ('edit_key', 'Primary Edit Key', 'Main editing key (usually G)'),
                ('secondary_edit_key', 'Secondary Edit Key', 'Secondary select/edit key (usually V)'),
                ('toggle_button', 'Spam Toggle Key', 'Hold this key to activate spam macro')
            ]),
            ("Combat Controls", [
                ('weapon_slot', 'Weapon Slot', 'Weapon slot number for auto pullout'),
                ('pickup_key', 'Pickup Key', 'Key for picking up items (usually E)'),
                ('pickup_trigger', 'Pickup Trigger', 'Hold this key to spam pickup')
            ]),
            ("Building Controls", [
                ('wall_button', 'Wall Placement Key', 'Secondary wall placement button'),
                ('wall_trigger', 'Wall Take Trigger', 'Key to trigger wall take sequence')
            ])
        ]
        
        for group_name, keybinds in keybind_groups:
            group_header = QLabel(group_name)
            group_header.setStyleSheet("""
                font-size: 18px; 
                font-weight: bold; 
                color: #007acc; 
                margin: 20px 0 10px 0; 
                padding-bottom: 5px;
                border-bottom: 2px solid #007acc;
            """)
            scroll_layout.addWidget(group_header)
            
            for key, label, description in keybinds:
                group = QFrame()
                group.setStyleSheet("QFrame { padding: 15px; margin: 5px 0; }")
                group_layout = QVBoxLayout(group)
                group_layout.setSpacing(8)
                
                label_layout = QHBoxLayout()
                label_widget = QLabel(label)
                label_widget.setStyleSheet("font-weight: bold; color: white; font-size: 15px;")
                
                desc_widget = QLabel(description)
                desc_widget.setStyleSheet("color: #aaaaaa; font-size: 12px; margin-left: 10px;")
                
                label_layout.addWidget(label_widget)
                label_layout.addStretch()
                label_layout.addWidget(desc_widget)
                
                input_layout = QHBoxLayout()
                input_layout.setSpacing(10)
                
                input_widget = ClickableLineEdit(self.keybinds[key])
                input_widget.setStyleSheet("""
                    QLineEdit {
                        font-size: 14px; 
                        padding: 12px 15px;
                        font-weight: bold;
                        text-align: center;
                        min-width: 100px;
                    }
                """)
                input_widget.setMaximumWidth(150)
                input_widget.setAlignment(Qt.AlignCenter)
                input_widget.textChanged.connect(lambda text, k=key: self.update_keybind(k, text))
                input_widget.clicked.connect(lambda k=key, w=input_widget: self.capture_key(k, w))
                
                capture_btn = QPushButton("Capture")
                capture_btn.setMaximumWidth(100)
                capture_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 12px;
                        padding: 8px 12px;
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #6c757d, stop:1 #5a6268);
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #7c858d, stop:1 #6a7278);
                    }
                """)
                capture_btn.clicked.connect(lambda checked, k=key, w=input_widget: self.capture_key(k, w))
                
                input_layout.addWidget(input_widget)
                input_layout.addWidget(capture_btn)
                input_layout.addStretch()
                
                group_layout.addLayout(label_layout)
                group_layout.addLayout(input_layout)
                
                self.keybind_inputs[key] = input_widget
                scroll_layout.addWidget(group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6c757d, stop:1 #5a6268);
                font-size: 14px;
                padding: 12px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7c858d, stop:1 #6a7278);
            }
        """)
        reset_btn.clicked.connect(self.reset_keybinds)
        
        save_button = QPushButton("Save Keybinds")
        save_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #218838);
                font-size: 16px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34ce57, stop:1 #28a745);
            }
        """)
        save_button.clicked.connect(self.save_settings_with_feedback)
        
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
        
        self.content_stack.addWidget(keybinds_page)
    
    def setup_status_page(self):
        status_page = QWidget()
        layout = QVBoxLayout(status_page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("System Status")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #007acc; margin-bottom: 10px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        system_frame = QFrame()
        system_frame.setStyleSheet("QFrame { padding: 20px; }")
        system_layout = QVBoxLayout(system_frame)
        
        system_title = QLabel("System Information")
        system_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 10px;")
        system_layout.addWidget(system_title)
        
        system_info = QLabel(f"""
        Application Version: 2.0.0 Professional
        Python Version: {sys.version.split()[0]}
        PySide6 Version: Available
        Pynput Version: Available
        Auto-Save: Enabled (5s interval)
        """)
        system_info.setStyleSheet("color: #cccccc; font-family: monospace; line-height: 1.6;")
        system_layout.addWidget(system_info)
        
        scroll_layout.addWidget(system_frame)
        
        scripts_frame = QFrame()
        scripts_frame.setStyleSheet("QFrame { padding: 20px; }")
        scripts_layout = QVBoxLayout(scripts_frame)
        
        scripts_title = QLabel("Script Status")
        scripts_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 10px;")
        scripts_layout.addWidget(scripts_title)
        
        self.script_status_labels = {}
        for script_id in self.script_states:
            status_label = QLabel(f"{script_id.replace('_', ' ').title()}: Inactive")
            status_label.setStyleSheet("color: #ff6b6b; font-family: monospace; margin: 5px 0;")
            self.script_status_labels[script_id] = status_label
            scripts_layout.addWidget(status_label)
        
        scroll_layout.addWidget(scripts_frame)
        
        keybind_frame = QFrame()
        keybind_frame.setStyleSheet("QFrame { padding: 20px; }")
        keybind_layout = QVBoxLayout(keybind_frame)
        
        keybind_title = QLabel("Current Keybinds")
        keybind_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 10px;")
        keybind_layout.addWidget(keybind_title)
        
        self.keybind_summary = QLabel()
        self.keybind_summary.setStyleSheet("color: #cccccc; font-family: monospace; line-height: 1.8;")
        keybind_layout.addWidget(self.keybind_summary)
        self.update_keybind_summary()
        
        scroll_layout.addWidget(keybind_frame)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self.refresh_status)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        self.content_stack.addWidget(status_page)
    
    def capture_key(self, key_name, input_widget):
        try:
            dialog = KeyCaptureDialog(self)
            if dialog.exec() == QDialog.Accepted and dialog.captured_key:
                input_widget.setText(dialog.captured_key)
                self.update_keybind(key_name, dialog.captured_key)
                self.save_settings()
        except Exception as e:
            print(f"Key capture error: {e}")
            QMessageBox.warning(self, "Error", f"Failed to capture key: {str(e)}")
    
    def reset_keybinds(self):
        reply = QMessageBox.question(self, 'Reset Keybinds', 
                                   'Are you sure you want to reset all keybinds to default values?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            default_keybinds = {
                'edit_key': 'g',
                'secondary_edit_key': 'v', 
                'toggle_button': 't',
                'weapon_slot': '2',
                'pickup_key': 'e',
                'pickup_trigger': 'f',
                'wall_button': 'p',
                'wall_trigger': 'r'
            }
            
            self.keybinds = default_keybinds.copy()
            
            for key, input_widget in self.keybind_inputs.items():
                input_widget.setText(self.keybinds[key])
            
            self.save_settings()
            self.update_keybind_summary()
            
            QMessageBox.information(self, "Success", "Keybinds have been reset to defaults!")
    
    def sidebar_changed(self, current, previous):
        if current:
            self.content_stack.setCurrentIndex(current.listWidget().row(current))
    
    def toggle_script(self, script_id, enabled):
        self.script_states[script_id] = enabled
        if not enabled and script_id in self.script_bot.active_scripts:
            self.script_bot.stop_script(script_id)
            self.update_script_status(script_id, "Inactive")
    
    def update_keybind(self, key, value):
        self.keybinds[key] = value.lower().strip()
        self.update_keybind_summary()
    
    def stop_all_scripts(self):
        self.script_bot.stop_all_scripts()
        
        for script_id, card in self.script_cards.items():
            card['checkbox'].setChecked(False)
            self.script_states[script_id] = False
        
        self.status_indicator.setText("Stopped")
        self.status_indicator.setStyleSheet("font-size: 16px; color: #dc3545; font-weight: bold;")
        
        QMessageBox.information(self, "Scripts Stopped", "All scripts have been stopped successfully.")
    
    def apply_scripts(self):
        try:
            self.script_bot.stop_all_scripts()
            
            enabled_count = 0
            
            if self.script_states['spam_macro']:
                self.script_bot.start_spam_macro(
                    self.keybinds['edit_key'],
                    self.keybinds['secondary_edit_key'],
                    self.keybinds['toggle_button']
                )
                enabled_count += 1
            
            if self.script_states['auto_pullout']:
                self.script_bot.start_auto_pullout(
                    self.keybinds['edit_key'],
                    self.keybinds['weapon_slot']
                )
                enabled_count += 1
            
            if self.script_states['auto_pickup']:
                self.script_bot.start_auto_pickup(
                    self.keybinds['pickup_key'],
                    self.keybinds['pickup_trigger']
                )
                enabled_count += 1
            
            if self.script_states['wall_take']:
                self.script_bot.start_wall_take(
                    self.keybinds['wall_button'],
                    self.keybinds['wall_trigger']
                )
                enabled_count += 1
            
            self.save_settings()
            
            if enabled_count > 0:
                self.status_indicator.setText(f"Active ({enabled_count})")
                self.status_indicator.setStyleSheet("font-size: 16px; color: #28a745; font-weight: bold;")
            else:
                self.status_indicator.setText("Ready")
                self.status_indicator.setStyleSheet("font-size: 16px; color: #007acc; font-weight: bold;")
            
            msg = QMessageBox()
            msg.setWindowTitle("Success")
            msg.setText(f"Configuration applied successfully!\n\n{enabled_count} script(s) are now active.")
            msg.setIcon(QMessageBox.Information)
            msg.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply scripts:\n{str(e)}")
    
    def update_script_status(self, script_id, status):
        if script_id in self.script_cards:
            status_label = self.script_cards[script_id]['status']
            status_label.setText(status)
            
            if status == "Inactive" or status == "Stopped":
                status_label.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 12px; margin-top: 5px;")
            elif "Ready" in status:
                status_label.setStyleSheet("color: #28a745; font-weight: bold; font-size: 12px; margin-top: 5px;")
            elif "Error" in status:
                status_label.setStyleSheet("color: #dc3545; font-weight: bold; font-size: 12px; margin-top: 5px;")
            else:
                status_label.setStyleSheet("color: #007acc; font-weight: bold; font-size: 12px; margin-top: 5px;")
        
        if script_id in self.script_status_labels:
            label = self.script_status_labels[script_id]
            label.setText(f"{script_id.replace('_', ' ').title()}: {status}")
            
            if status == "Inactive" or status == "Stopped":
                label.setStyleSheet("color: #ff6b6b; font-family: monospace; margin: 5px 0;")
            elif "Ready" in status:
                label.setStyleSheet("color: #28a745; font-family: monospace; margin: 5px 0;")
            elif "Error" in status:
                label.setStyleSheet("color: #dc3545; font-family: monospace; margin: 5px 0;")
            else:
                label.setStyleSheet("color: #007acc; font-family: monospace; margin: 5px 0;")
    
    def update_keybind_summary(self):
        if hasattr(self, 'keybind_summary'):
            summary_text = ""
            for key, value in self.keybinds.items():
                display_name = key.replace('_', ' ').title()
                summary_text += f"{display_name:20}: {value.upper()}\n"
            
            self.keybind_summary.setText(summary_text.strip())
    
    def refresh_status(self):
        self.update_keybind_summary()
        
        active_count = sum(1 for active in self.script_bot.active_scripts.values() if active)
        if active_count > 0:
            self.status_indicator.setText(f"Active ({active_count})")
            self.status_indicator.setStyleSheet("font-size: 16px; color: #28a745; font-weight: bold;")
        else:
            self.status_indicator.setText("Ready")
            self.status_indicator.setStyleSheet("font-size: 16px; color: #007acc; font-weight: bold;")
    
    def save_settings_with_feedback(self):
        self.save_settings()
        QMessageBox.information(self, "Saved", "Keybinds have been saved successfully!")
    
    def save_settings(self):
        settings = {
            'keybinds': self.keybinds,
            'script_states': self.script_states,
            'version': '2.0.0'
        }
        
        try:
            settings_file = Path('keybind_manager_settings.json')
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
            QMessageBox.warning(self, "Save Error", f"Failed to save settings:\n{str(e)}")
    
    def load_settings(self):
        try:
            settings_file = Path('keybind_manager_settings.json')
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                    if 'keybinds' in settings:
                        self.keybinds.update(settings['keybinds'])
                    
                    if 'script_states' in settings:
                        self.script_states.update(settings['script_states'])
                        
                print("Settings loaded successfully")
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def closeEvent(self, event):
        self.script_bot.stop_all_scripts()
        self.save_settings()
        
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        
        event.accept()


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        app.setApplicationName("Professional Keybind Manager")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("Gaming Tools")
        
        window = FortniteScriptGUI()
        window.show()
        
        screen = app.primaryScreen().geometry()
        window_geo = window.geometry()
        x = (screen.width() - window_geo.width()) // 2
        y = (screen.height() - window_geo.height()) // 2
        window.move(x, y)
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Application error: {e}")
        QMessageBox.critical(None, "Fatal Error", f"Failed to start application:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()