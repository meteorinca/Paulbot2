# robot.py - High-Level Robot Orchestration
# ==========================================
import time
from servos import ServoController
from display import EyeAnimation
from gaits import GaitController

class Robot:
    """Main robot class that orchestrates all subsystems."""
    
    def __init__(self):
        print("Initializing Robot...")
        self.servos = ServoController()
        self.eyes = EyeAnimation()
        self.gait = GaitController(self.servos)
        
        self.last_update = time.ticks_ms()
        self.running = False
        print("Robot initialized!")
    
    def start(self):
        """Start the robot in default state."""
        self.running = True
        self.gait.set_pose("stand")
        self.eyes.set_animation("idle")
    
    def stop(self):
        """Stop all robot activity."""
        self.running = False
        self.gait.stop_all()
        self.servos.detach_all()
    
    def update(self):
        """Main update loop - call frequently."""
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_update) / 1000.0
        self.last_update = now
        
        self.gait.update(dt)
        self.servos.update_all(dt)
        self.eyes.update()
    
    # Movement commands
    def forward(self, speed=1.0):
        self.gait.start_walk(1, 0, speed)
        self.eyes.set_animation("idle")
    
    def backward(self, speed=1.0):
        self.gait.start_walk(-1, 0, speed)
        self.eyes.look_at(0, 0.5)
    
    def left(self, speed=1.0):
        self.gait.start_walk(1, -1, speed)
        self.eyes.look_at(-0.5, 0)
    
    def right(self, speed=1.0):
        self.gait.start_walk(1, 1, speed)
        self.eyes.look_at(0.5, 0)
    
    def halt(self):
        self.gait.stop_walk()
        self.eyes.set_animation("idle")
    
    # Poses
    def stand(self):
        self.gait.set_pose("stand")
    
    def sit(self):
        self.gait.set_pose("sit")
        self.eyes.set_animation("happy", 1000)
    
    def crouch(self):
        self.gait.set_pose("crouch")
    
    # Actions
    def wave(self):
        self.gait.wave()
        self.eyes.set_animation("happy", 2000)
    
    def bow(self):
        self.gait.bow()
        self.eyes.set_animation("happy", 1500)
    
    def shake(self):
        self.gait.shake()
        self.eyes.set_animation("dizzy", 1500)
    
    def wiggle(self):
        self.gait.wiggle()
        self.eyes.set_animation("happy", 1000)
    
    # Eye expressions
    def happy(self):
        self.eyes.set_animation("happy", 2000)
    
    def sad(self):
        self.eyes.set_animation("sad", 2000)
    
    def angry(self):
        self.eyes.set_animation("angry", 2000)
    
    def sleep(self):
        self.eyes.set_animation("sleep")
    
    def wake(self):
        self.eyes.set_animation("surprised", 500)
    
    # Servo direct control
    def set_servo(self, name, angle):
        self.servos.set_servo(name, angle)
    
    def center_all(self):
        self.servos.center_all()


# Test
if __name__ == "__main__":
    bot = Robot()
    bot.start()
    
    print("Testing movements...")
    bot.wave()
    for _ in range(100):
        bot.update()
        time.sleep_ms(20)
    
    bot.stand()
    print("Done!")
