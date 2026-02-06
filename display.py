# display.py - OLED Display Module for Robot Eyes
# ================================================
# Non-blocking eye animations for the robot's OLED display.
# Uses SSD1306 driver for 128x64 I2C OLED.

from machine import Pin, I2C
import time
import math

# Import display pins from config
from servo_config import OLED_SCL_PIN, OLED_SDA_PIN, OLED_WIDTH, OLED_HEIGHT

# Try to import SSD1306 driver
try:
    import ssd1306
    SSD1306_AVAILABLE = True
except ImportError:
    SSD1306_AVAILABLE = False
    print("Warning: ssd1306 module not found. Display disabled.")


class EyeAnimation:
    """
    Non-blocking eye animation system.
    
    Eyes are drawn as two circles with pupils that can move,
    blink, and show various expressions.
    """
    
    # Eye positions (center of each eye)
    LEFT_EYE_X = 32
    RIGHT_EYE_X = 96
    EYE_Y = 32
    
    # Eye dimensions
    EYE_RADIUS = 20
    PUPIL_RADIUS = 8
    
    # Animation states
    STATE_IDLE = "idle"
    STATE_BLINK = "blink"
    STATE_LOOK_LEFT = "look_left"
    STATE_LOOK_RIGHT = "look_right"
    STATE_LOOK_UP = "look_up"
    STATE_LOOK_DOWN = "look_down"
    STATE_HAPPY = "happy"
    STATE_SAD = "sad"
    STATE_ANGRY = "angry"
    STATE_SURPRISED = "surprised"
    STATE_SLEEP = "sleep"
    STATE_WINK = "wink"
    STATE_HEART = "heart"
    STATE_DIZZY = "dizzy"
    STATE_SQUINT = "squint"
    
    def __init__(self):
        """Initialize the display and animation state."""
        self.display = None
        self.enabled = False
        
        if SSD1306_AVAILABLE:
            try:
                i2c = I2C(0, scl=Pin(OLED_SCL_PIN), sda=Pin(OLED_SDA_PIN))
                self.display = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
                self.enabled = True
                print("OLED display initialized")
            except Exception as e:
                print(f"Failed to initialize display: {e}")
        
        # Animation state
        self.current_state = self.STATE_IDLE
        self.state_start_time = time.ticks_ms()
        self.state_duration = 0  # 0 = infinite
        self.return_state = self.STATE_IDLE
        
        # Pupil position (offset from center, -1.0 to 1.0)
        self.pupil_x = 0.0
        self.pupil_y = 0.0
        self.target_pupil_x = 0.0
        self.target_pupil_y = 0.0
        
        # Blink state
        self.blink_progress = 0.0  # 0.0 = open, 1.0 = closed
        self.left_blink = 0.0
        self.right_blink = 0.0
        
        # Animation timing
        self.last_update = time.ticks_ms()
        self.auto_blink_interval = 3000  # ms between auto blinks
        self.last_blink = time.ticks_ms()
        self.animation_frame = 0
        
        # Clear display on init
        if self.enabled:
            self.clear()
            self.draw_idle()
            self.show()
    
    def clear(self):
        """Clear the display buffer."""
        if self.enabled and self.display:
            self.display.fill(0)
    
    def show(self):
        """Update the physical display from buffer."""
        if self.enabled and self.display:
            self.display.show()
    
    def draw_circle(self, cx, cy, r, fill=False):
        """Draw a circle at center (cx, cy) with radius r."""
        if not self.enabled:
            return
            
        if fill:
            # Filled circle using horizontal lines
            for y in range(-r, r + 1):
                x = int(math.sqrt(r * r - y * y))
                self.display.hline(cx - x, cy + y, 2 * x + 1, 1)
        else:
            # Outline only using Bresenham's circle
            x = 0
            y = r
            d = 3 - 2 * r
            while y >= x:
                # Draw 8 symmetric points
                self.display.pixel(cx + x, cy + y, 1)
                self.display.pixel(cx - x, cy + y, 1)
                self.display.pixel(cx + x, cy - y, 1)
                self.display.pixel(cx - x, cy - y, 1)
                self.display.pixel(cx + y, cy + x, 1)
                self.display.pixel(cx - y, cy + x, 1)
                self.display.pixel(cx + y, cy - x, 1)
                self.display.pixel(cx - y, cy - x, 1)
                
                if d < 0:
                    d = d + 4 * x + 6
                else:
                    d = d + 4 * (x - y) + 10
                    y -= 1
                x += 1
    
    def draw_eye(self, cx, cy, blink_amount=0.0, pupil_offset_x=0, pupil_offset_y=0,
                 expression="normal"):
        """
        Draw a single eye.
        
        Args:
            cx, cy: Center position
            blink_amount: 0.0 = open, 1.0 = closed
            pupil_offset_x/y: Pupil offset in pixels
            expression: "normal", "happy", "sad", "angry", "surprised"
        """
        if not self.enabled:
            return
        
        # Calculate blink effect (squeeze from top and bottom)
        open_height = int(self.EYE_RADIUS * (1 - blink_amount))
        
        if blink_amount >= 0.9:
            # Eye closed - just draw a line
            self.display.hline(cx - self.EYE_RADIUS, cy, self.EYE_RADIUS * 2, 1)
            return
        
        # Draw eye outline (ellipse when blinking)
        if blink_amount > 0.1:
            # Simplified ellipse as we blink
            for angle in range(0, 360, 5):
                rad = math.radians(angle)
                x = int(cx + self.EYE_RADIUS * math.cos(rad))
                y = int(cy + open_height * math.sin(rad))
                self.display.pixel(x, y, 1)
        else:
            # Full circle when open
            self.draw_circle(cx, cy, self.EYE_RADIUS, fill=False)
        
        # Expression modifiers
        if expression == "happy":
            # Draw curved line at bottom (happy eye)
            for x in range(-10, 11):
                y = int(5 - (x * x) / 20)
                self.display.pixel(cx + x, cy + 5 - y, 1)
            return  # No pupil for happy eyes
        
        elif expression == "sad":
            # Droopy eyelid at top
            for x in range(-self.EYE_RADIUS, 0):
                y = int(abs(x) / 4)
                self.display.hline(cx + x, cy - self.EYE_RADIUS + y, 1, 1)
        
        elif expression == "angry":
            # Angled eyebrows
            self.display.line(cx - 15, cy - 22, cx + 5, cy - 28, 1)
        
        elif expression == "surprised":
            # Bigger eye
            self.draw_circle(cx, cy, self.EYE_RADIUS + 5, fill=False)
        
        # Draw pupil (unless happy expression)
        pupil_x = cx + int(pupil_offset_x * (self.EYE_RADIUS - self.PUPIL_RADIUS - 2))
        pupil_y = cy + int(pupil_offset_y * (open_height - self.PUPIL_RADIUS - 2))
        
        # Clamp pupil position
        max_offset = self.EYE_RADIUS - self.PUPIL_RADIUS - 2
        dx = pupil_x - cx
        dy = pupil_y - cy
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > max_offset:
            scale = max_offset / dist
            pupil_x = int(cx + dx * scale)
            pupil_y = int(cy + dy * scale)
        
        self.draw_circle(pupil_x, pupil_y, self.PUPIL_RADIUS, fill=True)
        
        # Add highlight to pupil
        self.display.pixel(pupil_x - 3, pupil_y - 3, 0)
        self.display.pixel(pupil_x - 2, pupil_y - 3, 0)
        self.display.pixel(pupil_x - 3, pupil_y - 2, 0)
    
    def draw_idle(self):
        """Draw default idle expression."""
        self.clear()
        self.draw_eye(self.LEFT_EYE_X, self.EYE_Y, self.left_blink, 
                      self.pupil_x, self.pupil_y)
        self.draw_eye(self.RIGHT_EYE_X, self.EYE_Y, self.right_blink,
                      self.pupil_x, self.pupil_y)
    
    def draw_happy(self):
        """Draw happy expression (^_^)."""
        self.clear()
        self.draw_eye(self.LEFT_EYE_X, self.EYE_Y, 0, 0, 0, "happy")
        self.draw_eye(self.RIGHT_EYE_X, self.EYE_Y, 0, 0, 0, "happy")
    
    def draw_sad(self):
        """Draw sad expression."""
        self.clear()
        self.draw_eye(self.LEFT_EYE_X, self.EYE_Y, 0.2, 0, 0.3, "sad")
        self.draw_eye(self.RIGHT_EYE_X, self.EYE_Y, 0.2, 0, 0.3, "sad")
    
    def draw_angry(self):
        """Draw angry expression."""
        self.clear()
        self.draw_eye(self.LEFT_EYE_X, self.EYE_Y, 0.3, 0, 0, "angry")
        self.draw_eye(self.RIGHT_EYE_X, self.EYE_Y, 0.3, 0, 0, "angry")
    
    def draw_surprised(self):
        """Draw surprised expression."""
        self.clear()
        self.draw_eye(self.LEFT_EYE_X, self.EYE_Y, 0, 0, 0, "surprised")
        self.draw_eye(self.RIGHT_EYE_X, self.EYE_Y, 0, 0, 0, "surprised")
    
    def draw_sleep(self):
        """Draw sleeping expression (closed eyes with Z's)."""
        self.clear()
        # Closed eyes (lines)
        self.display.hline(self.LEFT_EYE_X - 15, self.EYE_Y, 30, 1)
        self.display.hline(self.RIGHT_EYE_X - 15, self.EYE_Y, 30, 1)
        
        # Z's floating
        offset = (self.animation_frame % 10) * 2
        self.display.text("Z", 100, 10 - offset % 20, 1)
        self.display.text("z", 110, 5 - (offset + 5) % 20, 1)
    
    def draw_wink(self):
        """Draw winking expression."""
        self.clear()
        self.draw_eye(self.LEFT_EYE_X, self.EYE_Y, 0.95, 0, 0)  # Closed
        self.draw_eye(self.RIGHT_EYE_X, self.EYE_Y, 0, 0, 0)     # Open
    
    def draw_heart(self):
        """Draw heart eyes."""
        self.clear()
        
        # Draw hearts instead of eyes
        for cx in [self.LEFT_EYE_X, self.RIGHT_EYE_X]:
            # Simple heart shape
            size = 12
            for y in range(size):
                for x in range(-size, size + 1):
                    # Heart equation
                    nx = x / size
                    ny = (y - size/2) / size
                    if (nx*nx + ny*ny - 1)**3 - nx*nx * ny*ny*ny < 0:
                        self.display.pixel(cx + x, self.EYE_Y - y + size//2, 1)
    
    def draw_dizzy(self):
        """Draw dizzy expression (spiral eyes)."""
        self.clear()
        
        # Spiral eyes
        for cx in [self.LEFT_EYE_X, self.RIGHT_EYE_X]:
            angle_offset = self.animation_frame * 20
            for i in range(0, 360 * 3, 15):
                angle = math.radians(i + angle_offset)
                r = i / 360 * 8
                x = int(cx + r * math.cos(angle))
                y = int(self.EYE_Y + r * math.sin(angle))
                self.display.pixel(x, y, 1)
    
    def draw_squint(self):
        """Draw squinting expression."""
        self.clear()
        self.draw_eye(self.LEFT_EYE_X, self.EYE_Y, 0.6, 0, 0)
        self.draw_eye(self.RIGHT_EYE_X, self.EYE_Y, 0.6, 0, 0)
    
    def set_animation(self, state, duration_ms=0, return_to=None):
        """
        Set the current animation state.
        
        Args:
            state: Animation state (use STATE_* constants)
            duration_ms: How long to show (0 = until changed)
            return_to: State to return to after duration (None = idle)
        """
        self.current_state = state
        self.state_start_time = time.ticks_ms()
        self.state_duration = duration_ms
        self.return_state = return_to if return_to else self.STATE_IDLE
        self.animation_frame = 0
    
    def look_at(self, x, y):
        """
        Set pupil target position.
        
        Args:
            x: Horizontal position (-1.0 = left, 1.0 = right)
            y: Vertical position (-1.0 = up, 1.0 = down)
        """
        self.target_pupil_x = max(-1.0, min(1.0, x))
        self.target_pupil_y = max(-1.0, min(1.0, y))
    
    def blink(self):
        """Trigger a blink animation."""
        self.set_animation(self.STATE_BLINK, 200)
    
    def update(self):
        """
        Update animation state. Call this frequently in main loop.
        
        This is non-blocking and handles all animation timing internally.
        """
        if not self.enabled:
            return
        
        current_time = time.ticks_ms()
        delta_ms = time.ticks_diff(current_time, self.last_update)
        self.last_update = current_time
        
        # Update animation frame counter
        self.animation_frame += 1
        
        # Check if current state duration has expired
        if self.state_duration > 0:
            elapsed = time.ticks_diff(current_time, self.state_start_time)
            if elapsed >= self.state_duration:
                self.current_state = self.return_state
                self.state_duration = 0
        
        # Auto-blink in idle state
        if self.current_state == self.STATE_IDLE:
            if time.ticks_diff(current_time, self.last_blink) > self.auto_blink_interval:
                self.blink()
                self.last_blink = current_time
        
        # Smooth pupil movement
        lerp_speed = 0.15
        self.pupil_x += (self.target_pupil_x - self.pupil_x) * lerp_speed
        self.pupil_y += (self.target_pupil_y - self.pupil_y) * lerp_speed
        
        # Handle blink animation
        if self.current_state == self.STATE_BLINK:
            elapsed = time.ticks_diff(current_time, self.state_start_time)
            # Blink is: close (100ms) then open (100ms)
            if elapsed < 100:
                self.left_blink = elapsed / 100.0
                self.right_blink = elapsed / 100.0
            else:
                progress = (elapsed - 100) / 100.0
                self.left_blink = 1.0 - progress
                self.right_blink = 1.0 - progress
        else:
            self.left_blink = 0.0
            self.right_blink = 0.0
        
        # Draw current state
        if self.current_state == self.STATE_IDLE or self.current_state == self.STATE_BLINK:
            self.draw_idle()
        elif self.current_state == self.STATE_LOOK_LEFT:
            self.target_pupil_x = -0.8
            self.draw_idle()
        elif self.current_state == self.STATE_LOOK_RIGHT:
            self.target_pupil_x = 0.8
            self.draw_idle()
        elif self.current_state == self.STATE_LOOK_UP:
            self.target_pupil_y = -0.8
            self.draw_idle()
        elif self.current_state == self.STATE_LOOK_DOWN:
            self.target_pupil_y = 0.8
            self.draw_idle()
        elif self.current_state == self.STATE_HAPPY:
            self.draw_happy()
        elif self.current_state == self.STATE_SAD:
            self.draw_sad()
        elif self.current_state == self.STATE_ANGRY:
            self.draw_angry()
        elif self.current_state == self.STATE_SURPRISED:
            self.draw_surprised()
        elif self.current_state == self.STATE_SLEEP:
            self.draw_sleep()
        elif self.current_state == self.STATE_WINK:
            self.draw_wink()
        elif self.current_state == self.STATE_HEART:
            self.draw_heart()
        elif self.current_state == self.STATE_DIZZY:
            self.draw_dizzy()
        elif self.current_state == self.STATE_SQUINT:
            self.draw_squint()
        
        self.show()
    
    def get_available_animations(self):
        """Return list of available animation names."""
        return [
            self.STATE_IDLE, self.STATE_BLINK, self.STATE_LOOK_LEFT,
            self.STATE_LOOK_RIGHT, self.STATE_LOOK_UP, self.STATE_LOOK_DOWN,
            self.STATE_HAPPY, self.STATE_SAD, self.STATE_ANGRY,
            self.STATE_SURPRISED, self.STATE_SLEEP, self.STATE_WINK,
            self.STATE_HEART, self.STATE_DIZZY, self.STATE_SQUINT
        ]


# Test if run directly
if __name__ == "__main__":
    print("Testing EyeAnimation...")
    eyes = EyeAnimation()
    
    if eyes.enabled:
        # Test each animation
        animations = eyes.get_available_animations()
        for anim in animations:
            print(f"Showing: {anim}")
            eyes.set_animation(anim, 1500)
            
            # Run update loop for duration
            start = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start) < 1500:
                eyes.update()
                time.sleep_ms(20)
        
        # Return to idle
        eyes.set_animation(eyes.STATE_IDLE)
        print("Test complete!")
    else:
        print("Display not available")
