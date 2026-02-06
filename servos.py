# servos.py - Servo Control Module for Quadruped Robot
# =====================================================
# Handles individual servo control with smooth movements,
# calibration, and safety limits.

from machine import Pin, PWM
import time
import math

# Import configuration from servo_config.py
from servo_config import (
    SERVO_PINS, SERVO_INVERTED, SERVO_LIMITS,
    SERVO_CENTER, SERVO_SPEED, SPEED_MULTIPLIER,
    ALL_SERVOS, FEMUR_SERVOS, KNEE_SERVOS, LEGS
)


class Servo:
    """
    Individual servo controller with angle conversion and smooth movement.
    
    Converts angles (0-180°) to PWM duty cycles for SG90/MG90S servos.
    Standard servo PWM: 50Hz, 0.5ms-2.5ms pulse width (500-2500µs)
    """
    
    # PWM parameters for servos (adjust if servos behave strangely)
    PWM_FREQ = 50       # Standard servo frequency
    MIN_US = 500        # Minimum pulse width in microseconds (0°)
    MAX_US = 2500       # Maximum pulse width in microseconds (180°)
    
    def __init__(self, name, pin_num, inverted=False, limits=(0, 180), center=90):
        """
        Initialize a servo.
        
        Args:
            name: Servo identifier (e.g., "R1", "L3")
            pin_num: GPIO pin number
            inverted: If True, reverse servo direction
            limits: Tuple of (min_angle, max_angle)
            center: Default center position
        """
        self.name = name
        self.pin_num = pin_num
        self.inverted = inverted
        self.min_angle, self.max_angle = limits
        self.center = center
        
        # Current state
        self.current_angle = center
        self.target_angle = center
        
        # Initialize PWM
        self.pwm = PWM(Pin(pin_num))
        self.pwm.freq(self.PWM_FREQ)
        
        # Move to center on init
        self._write_angle(center)
    
    def _angle_to_duty(self, angle):
        """
        Convert angle (0-180) to PWM duty cycle (0-65535 for ESP32).
        
        The math:
        - pulse_width = map(angle, 0, 180, MIN_US, MAX_US)
        - duty = pulse_width / period * 65535
        - period = 1/50Hz = 20ms = 20000µs
        """
        # Handle inversion
        if self.inverted:
            angle = 180 - angle
        
        # Map angle to pulse width
        pulse_us = self.MIN_US + (angle / 180.0) * (self.MAX_US - self.MIN_US)
        
        # Convert to duty cycle (ESP32 uses 16-bit duty: 0-65535)
        period_us = 1_000_000 / self.PWM_FREQ  # 20000µs for 50Hz
        duty = int((pulse_us / period_us) * 65535)
        
        return duty
    
    def _write_angle(self, angle):
        """Write angle to servo immediately (no smoothing)."""
        # Clamp to limits
        angle = max(self.min_angle, min(self.max_angle, angle))
        
        duty = self._angle_to_duty(angle)
        self.pwm.duty_u16(duty)
        self.current_angle = angle
    
    def set_angle(self, angle, immediate=True):
        """
        Set target angle for servo.
        
        Args:
            angle: Target angle (0-180)
            immediate: If True, move immediately; if False, use smooth motion
        """
        # Clamp to limits
        angle = max(self.min_angle, min(self.max_angle, angle))
        self.target_angle = angle
        
        if immediate:
            self._write_angle(angle)
    
    def update(self, delta_time, speed=None):
        """
        Update servo position for smooth movement.
        
        Call this in main loop for interpolated motion.
        
        Args:
            delta_time: Time since last update (seconds)
            speed: Movement speed in degrees/second (None = use config)
            
        Returns:
            True if still moving, False if at target
        """
        if speed is None:
            speed = SERVO_SPEED.get(self.name, 0.15) * 360 * SPEED_MULTIPLIER
        
        if abs(self.current_angle - self.target_angle) < 0.5:
            return False
        
        # Calculate step size
        max_step = speed * delta_time
        diff = self.target_angle - self.current_angle
        step = max(-max_step, min(max_step, diff))
        
        new_angle = self.current_angle + step
        self._write_angle(new_angle)
        
        return True
    
    def detach(self):
        """Stop PWM signal (servo will be free to move)."""
        self.pwm.duty_u16(0)
    
    def attach(self):
        """Re-enable PWM signal at current angle."""
        self._write_angle(self.current_angle)


class ServoController:
    """
    Manages all 8 servos of the quadruped robot.
    
    Provides high-level control for individual servos, legs,
    and coordinated movements.
    """
    
    def __init__(self):
        """Initialize all servos from configuration."""
        self.servos = {}
        
        for name in ALL_SERVOS:
            pin = SERVO_PINS[name]
            inverted = SERVO_INVERTED.get(name, False)
            limits = SERVO_LIMITS.get(name, (0, 180))
            center = SERVO_CENTER.get(name, 90)
            
            self.servos[name] = Servo(
                name=name,
                pin_num=pin,
                inverted=inverted,
                limits=limits,
                center=center
            )
            
        print(f"ServoController initialized with {len(self.servos)} servos")
    
    def get_servo(self, name):
        """Get individual servo by name."""
        return self.servos.get(name)
    
    def set_servo(self, name, angle, immediate=True):
        """
        Set single servo angle.
        
        Args:
            name: Servo name (e.g., "R1", "L3")
            angle: Target angle (0-180)
            immediate: Move immediately or smooth
        """
        if name in self.servos:
            self.servos[name].set_angle(angle, immediate)
    
    def set_leg(self, leg_name, femur_angle, knee_angle, immediate=True):
        """
        Set angles for a complete leg.
        
        Args:
            leg_name: "FR", "FL", "BR", or "BL"
            femur_angle: Femur servo angle
            knee_angle: Knee servo angle
            immediate: Move immediately or smooth
        """
        if leg_name in LEGS:
            femur_name, knee_name = LEGS[leg_name]
            self.set_servo(femur_name, femur_angle, immediate)
            self.set_servo(knee_name, knee_angle, immediate)
    
    def set_all(self, angle, immediate=True):
        """Set all servos to the same angle."""
        for servo in self.servos.values():
            servo.set_angle(angle, immediate)
    
    def center_all(self, immediate=True):
        """Move all servos to their center positions."""
        for name, servo in self.servos.items():
            servo.set_angle(SERVO_CENTER[name], immediate)
    
    def update_all(self, delta_time):
        """
        Update all servos for smooth movement.
        
        Args:
            delta_time: Time since last update (seconds)
            
        Returns:
            True if any servo is still moving
        """
        moving = False
        for servo in self.servos.values():
            if servo.update(delta_time):
                moving = True
        return moving
    
    def set_positions(self, positions, immediate=True):
        """
        Set multiple servos at once.
        
        Args:
            positions: Dict of {servo_name: angle}
            immediate: Move immediately or smooth
        """
        for name, angle in positions.items():
            self.set_servo(name, angle, immediate)
    
    def get_positions(self):
        """Get current positions of all servos."""
        return {name: servo.current_angle for name, servo in self.servos.items()}
    
    def get_targets(self):
        """Get target positions of all servos."""
        return {name: servo.target_angle for name, servo in self.servos.items()}
    
    def detach_all(self):
        """Detach all servos (stop PWM signals)."""
        for servo in self.servos.values():
            servo.detach()
        print("All servos detached")
    
    def attach_all(self):
        """Re-attach all servos."""
        for servo in self.servos.values():
            servo.attach()
        print("All servos attached")


# Quick test if run directly
if __name__ == "__main__":
    print("Testing ServoController...")
    controller = ServoController()
    
    # Center all
    print("Centering all servos...")
    controller.center_all()
    time.sleep(1)
    
    # Test each servo briefly
    for name in ALL_SERVOS:
        print(f"Testing {name}...")
        controller.set_servo(name, 70)
        time.sleep(0.3)
        controller.set_servo(name, 110)
        time.sleep(0.3)
        controller.set_servo(name, 90)
        time.sleep(0.3)
    
    print("Test complete!")
