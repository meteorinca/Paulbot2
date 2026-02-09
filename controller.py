# controller.py - PC-Side Robot Controller
# ==========================================
# Run this on your PC to control the robot via UDP

import socket
import sys
import time

class RobotController:
    """Simple UDP controller for the quadruped robot."""
    
    def __init__(self, robot_ip, port=5005):
        self.robot_ip = robot_ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1.0)
    
    def send(self, command):
        """Send command and get response."""
        try:
            self.sock.sendto(command.encode(), (self.robot_ip, self.port))
            data, _ = self.sock.recvfrom(256)
            return data.decode()
        except socket.timeout:
            return "TIMEOUT"
        except Exception as e:
            return f"ERROR: {e}"
    
    def interactive(self):
        """Interactive command mode."""
        print(f"\nConnected to robot at {self.robot_ip}:{self.port}")
        print("Commands: fwd, back, left, right, stop")
        print("          stand, sit, wave, bow, shake, wiggle")
        print("          happy, sad, angry, sleep, wake")
        print("          servo <name> <angle>, center")
        print("          help, quit\n")
        
        while True:
            try:
                cmd = input(">> ").strip()
                if not cmd:
                    continue
                if cmd.lower() == "quit" or cmd.lower() == "exit":
                    break
                
                response = self.send(cmd)
                print(f"   {response}")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
        
        self.send("stop")
        print("Disconnected.")


def wasd_control(controller):
    """WASD keyboard control (Windows only)."""
    try:
        import msvcrt
    except ImportError:
        print("WASD mode only works on Windows")
        return
    
    print("\nWASD Control Mode")
    print("W=forward, S=back, A=left, D=right, Space=stop, Q=quit")
    
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch().decode().lower()
            
            if key == 'w':
                print("Forward")
                controller.send("fwd")
            elif key == 's':
                print("Backward")
                controller.send("back")
            elif key == 'a':
                print("Left")
                controller.send("left")
            elif key == 'd':
                print("Right")
                controller.send("right")
            elif key == ' ':
                print("Stop")
                controller.send("stop")
            elif key == '1':
                controller.send("wave")
            elif key == '2':
                controller.send("bow")
            elif key == '3':
                controller.send("shake")
            elif key == 'q':
                controller.send("stop")
                break
        
        time.sleep(0.05)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python controller.py <robot_ip> [mode]")
        print("  mode: interactive (default) or wasd")
        sys.exit(1)
    
    robot_ip = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "interactive"
    
    ctrl = RobotController(robot_ip)
    
    # Test connection
    print(f"Connecting to {robot_ip}...")
    response = ctrl.send("ping")
    if "TIMEOUT" in response:
        print("Robot not responding. Check IP and ensure robot is running.")
        sys.exit(1)
    print(f"Robot status: {response}")
    
    if mode == "wasd":
        wasd_control(ctrl)
    else:
        ctrl.interactive()
