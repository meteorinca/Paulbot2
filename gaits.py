# gaits.py - Quadruped Gait Patterns
# ===================================
import time
import math
from servo_config import GAIT, LEGS, SERVO_CENTER

class GaitController:
    """Controls walking gaits and movement patterns."""
    
    def __init__(self, servo_controller):
        self.servos = servo_controller
        self.is_walking = False
        self.walk_phase = 0.0
        self.walk_speed = 1.0
        self.walk_direction = 0
        self.turn_direction = 0 
        
        self.is_moving = False
        self.movement_queue = []
        self.current_movement = None
        self.movement_start_time = 0
        self.movement_duration = 0
        
        # Gait parameters
        self.stand_femur = GAIT.get("STAND_FEMUR", 90)
        self.stand_knee = GAIT.get("STAND_KNEE", 180)
        self.step_lift = GAIT.get("STEP_LIFT", 110)
        self.step_plant = GAIT.get("STEP_PLANT", 180)
        self.step_fwd = GAIT.get("STEP_FWD", 115)
        self.step_back = GAIT.get("STEP_BACK", 65)
    
    def get_pose(self, name):
        """Get servo positions for named pose."""
        poses = {
            "neutral": {"R1":90,"R2":90,"L1":90,"L2":90,"R3":90,"R4":90,"L3":90,"L4":90},
            "stand": {"R1":self.stand_femur,"R2":self.stand_femur,"L1":self.stand_femur,"L2":self.stand_femur,
                     "R3":self.stand_knee,"R4":self.stand_knee,"L3":self.stand_knee,"L4":self.stand_knee},
            "sit": {"R1":90,"R2":90,"L1":90,"L2":90,"R3":45,"R4":45,"L3":45,"L4":45},
            "tall": {"R1":90,"R2":90,"L1":90,"L2":90,"R3":180,"R4":180,"L3":180,"L4":180},
            "crouch": {"R1":90,"R2":90,"L1":90,"L2":90,"R3":120,"R4":120,"L3":120,"L4":120},
        }
        return poses.get(name, poses["neutral"])
    
    def set_pose(self, name, immediate=True):
        """Set robot to predefined pose."""
        self.servos.set_positions(self.get_pose(name), immediate)
    
    def get_walk_positions(self, phase, direction=1, turn=0):
        """Calculate servo positions for walk cycle phase."""
        phase = phase % 1.0
        swing = (self.step_fwd - self.step_back) / 2
        center = (self.step_fwd + self.step_back) / 2
        
        # Tripod gait: Group A (FR+BL), Group B (FL+BR)
        femur_a = center + math.sin(phase * 2 * math.pi) * swing * direction
        femur_b = center + math.sin((phase + 0.5) * 2 * math.pi) * swing * direction
        
        knee_a = self.step_plant + max(0, math.sin(phase * 2 * math.pi)) * (self.step_lift - self.step_plant)
        knee_b = self.step_plant + max(0, math.sin((phase + 0.5) * 2 * math.pi)) * (self.step_lift - self.step_plant)
        
        turn_bias = 15 * turn
        return {
            "R1": femur_a - turn_bias, "R3": knee_a,
            "L2": femur_a + turn_bias, "L4": knee_a,
            "L1": femur_b + turn_bias, "L3": knee_b,
            "R2": femur_b - turn_bias, "R4": knee_b,
        }
    
    def start_walk(self, direction=1, turn=0, speed=1.0):
        self.is_walking = True
        self.walk_direction = direction
        self.turn_direction = turn
        self.walk_speed = speed
    
    def stop_walk(self):
        self.is_walking = False
        self.set_pose("stand", False)
    
    def update_walk(self, dt):
        if not self.is_walking:
            return
        self.walk_phase += dt / (0.8 / self.walk_speed)
        if self.walk_phase >= 1.0:
            self.walk_phase -= 1.0
        self.servos.set_positions(self.get_walk_positions(self.walk_phase, self.walk_direction, self.turn_direction), True)
    
    # Special movements
    def wave(self):
        self._queue([
            ({"R1":90,"R3":45}, 0.3), ({"R1":60}, 0.2), ({"R1":120}, 0.2),
            ({"R1":60}, 0.2), ({"R1":120}, 0.2), ({"R1":90,"R3":self.stand_knee}, 0.3),
        ])
    
    def bow(self):
        self._queue([
            ({"R3":120,"L3":120,"R4":160,"L4":160}, 0.5),
            (None, 0.5), (self.get_pose("stand"), 0.5),
        ])
    
    def shake(self):
        self._queue([
            ({"R1":70,"R2":70,"L1":110,"L2":110}, 0.15),
            ({"R1":110,"R2":110,"L1":70,"L2":70}, 0.15),
        ] * 3 + [(self.get_pose("stand"), 0.3)])
    
    def wiggle(self):
        self._queue([
            ({"R2":70,"L2":110}, 0.1), ({"R2":110,"L2":70}, 0.1),
        ] * 3 + [({"R2":90,"L2":90}, 0.2)])
    
    def _queue(self, seq):
        self.movement_queue = seq.copy()
        self.is_moving = True
        self._next()
    
    def _next(self):
        if not self.movement_queue:
            self.is_moving = False
            return False
        self.current_movement = self.movement_queue.pop(0)
        pos, dur = self.current_movement
        if pos:
            self.servos.set_positions(pos, True)
        self.movement_start_time = time.ticks_ms()
        self.movement_duration = int(dur * 1000)
        return True
    
    def update(self, dt):
        if self.is_walking:
            self.update_walk(dt)
        elif self.is_moving:
            if time.ticks_diff(time.ticks_ms(), self.movement_start_time) >= self.movement_duration:
                self._next()
    
    def stop_all(self):
        self.is_walking = False
        self.is_moving = False
        self.movement_queue = []
