"""
Input Controller for Aqueduct Automation
Handles actual mouse clicks and keyboard input
"""

import time
import logging
from typing import Tuple, Optional
import sys
import os

# Try to import PyAutoGUI for input control
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    # Configure PyAutoGUI
    pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
    pyautogui.PAUSE = 0.1      # Small pause between actions
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# Try to import pynput as alternative
try:
    from pynput import mouse, keyboard
    from pynput.mouse import Button, Listener as MouseListener
    from pynput.keyboard import Key, Listener as KeyboardListener
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

class InputController:
    """Handles mouse and keyboard input for automation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.input_method = self._detect_input_method()
        self.logger.info(f"Input method: {self.input_method}")
        
        if self.input_method == "none":
            self.logger.error("No input libraries available! Install PyAutoGUI or pynput")
            self.logger.error("Run: pip install pyautogui")
        
        # Input safety settings
        self.min_click_delay = 0.05  # Minimum delay between clicks
        self.last_click_time = 0
        self.last_key_time = 0
        
        # Initialize input controllers
        if self.input_method == "pynput":
            self.mouse_controller = mouse.Controller()
            self.keyboard_controller = keyboard.Controller()
    
    def _detect_input_method(self) -> str:
        """Detect which input method is available"""
        if PYAUTOGUI_AVAILABLE:
            return "pyautogui"
        elif PYNPUT_AVAILABLE:
            return "pynput"
        else:
            return "none"
    
    def click_position(self, x: int, y: int, button: str = "left") -> bool:
        """Click at specific screen coordinates"""
        try:
            if self.input_method == "none":
                self.logger.debug(f"Simulated click at ({x}, {y}) - no input library")
                return False
            
            # Respect minimum click delay
            current_time = time.time()
            if current_time - self.last_click_time < self.min_click_delay:
                time.sleep(self.min_click_delay - (current_time - self.last_click_time))
            
            if self.input_method == "pyautogui":
                pyautogui.click(x, y, button=button)
                self.logger.debug(f"PyAutoGUI click at ({x}, {y})")
                
            elif self.input_method == "pynput":
                # Move mouse to position and click
                self.mouse_controller.position = (x, y)
                time.sleep(0.01)  # Small delay for mouse movement
                
                if button == "left":
                    self.mouse_controller.click(Button.left)
                elif button == "right":
                    self.mouse_controller.click(Button.right)
                else:
                    self.mouse_controller.click(Button.left)
                
                self.logger.debug(f"Pynput click at ({x}, {y})")
            
            self.last_click_time = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Error clicking at ({x}, {y}): {e}")
            return False
    
    def send_key(self, key: str) -> bool:
        """Send a key press"""
        try:
            if self.input_method == "none":
                self.logger.debug(f"Simulated key press: {key}")
                return False
            
            # Respect minimum key delay
            current_time = time.time()
            if current_time - self.last_key_time < self.min_click_delay:
                time.sleep(self.min_click_delay - (current_time - self.last_key_time))
            
            if self.input_method == "pyautogui":
                pyautogui.press(key)
                self.logger.debug(f"PyAutoGUI key press: {key}")
                
            elif self.input_method == "pynput":
                # Convert key string to pynput key
                pynput_key = self._convert_key_to_pynput(key)
                if pynput_key:
                    self.keyboard_controller.press(pynput_key)
                    self.keyboard_controller.release(pynput_key)
                    self.logger.debug(f"Pynput key press: {key}")
                else:
                    self.logger.warning(f"Unknown key: {key}")
                    return False
            
            self.last_key_time = time.time()
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending key {key}: {e}")
            return False
    
    def _convert_key_to_pynput(self, key: str):
        """Convert key string to pynput key object"""
        # Handle special keys
        special_keys = {
            'escape': Key.esc,
            'enter': Key.enter,
            'space': Key.space,
            'tab': Key.tab,
            'shift': Key.shift,
            'ctrl': Key.ctrl,
            'alt': Key.alt,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
            'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
            'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
        }
        
        key_lower = key.lower()
        if key_lower in special_keys:
            return special_keys[key_lower]
        
        # Handle regular keys (single character)
        if len(key) == 1:
            return key.lower()
        
        return None
    
    def hold_key(self, key: str, duration: float = 0.1) -> bool:
        """Hold a key for a specified duration"""
        try:
            if self.input_method == "none":
                self.logger.debug(f"Simulated key hold: {key} for {duration}s")
                return False
            
            if self.input_method == "pyautogui":
                pyautogui.keyDown(key)
                time.sleep(duration)
                pyautogui.keyUp(key)
                self.logger.debug(f"PyAutoGUI key hold: {key} for {duration}s")
                
            elif self.input_method == "pynput":
                pynput_key = self._convert_key_to_pynput(key)
                if pynput_key:
                    self.keyboard_controller.press(pynput_key)
                    time.sleep(duration)
                    self.keyboard_controller.release(pynput_key)
                    self.logger.debug(f"Pynput key hold: {key} for {duration}s")
                else:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error holding key {key}: {e}")
            return False
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        try:
            if self.input_method == "pyautogui":
                return pyautogui.position()
            elif self.input_method == "pynput":
                return self.mouse_controller.position
            else:
                return (0, 0)
                
        except Exception as e:
            self.logger.error(f"Error getting mouse position: {e}")
            return (0, 0)
    
    def move_mouse(self, x: int, y: int, duration: float = 0.1) -> bool:
        """Move mouse to position smoothly"""
        try:
            if self.input_method == "none":
                return False
            
            if self.input_method == "pyautogui":
                pyautogui.moveTo(x, y, duration=duration)
                return True
            elif self.input_method == "pynput":
                self.mouse_controller.position = (x, y)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error moving mouse to ({x}, {y}): {e}")
            return False
    
    def scroll(self, x: int, y: int, clicks: int = 1) -> bool:
        """Scroll at position"""
        try:
            if self.input_method == "none":
                return False
            
            if self.input_method == "pyautogui":
                pyautogui.scroll(clicks, x=x, y=y)
                return True
            elif self.input_method == "pynput":
                self.mouse_controller.position = (x, y)
                self.mouse_controller.scroll(0, clicks)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error scrolling at ({x}, {y}): {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if input controller is available"""
        return self.input_method != "none"
    
    def get_method(self) -> str:
        """Get current input method"""
        return self.input_method

# Global input controller instance
_input_controller = None

def get_input_controller() -> InputController:
    """Get the global input controller instance"""
    global _input_controller
    if _input_controller is None:
        _input_controller = InputController()
    return _input_controller

# Convenience functions
def click_position(x: int, y: int, button: str = "left") -> bool:
    """Click at position using global input controller"""
    return get_input_controller().click_position(x, y, button)

def send_key(key: str) -> bool:
    """Send key using global input controller"""
    return get_input_controller().send_key(key)

def hold_key(key: str, duration: float = 0.1) -> bool:
    """Hold key using global input controller"""
    return get_input_controller().hold_key(key, duration)

def move_mouse(x: int, y: int, duration: float = 0.1) -> bool:
    """Move mouse using global input controller"""
    return get_input_controller().move_mouse(x, y, duration) 