# udp_server.py - UDP Network Control Server
# ===========================================
import socket
import json
import time

class UDPServer:
    """Non-blocking UDP server for robot control commands."""
    
    def __init__(self, robot, port=5005):
        self.robot = robot
        self.port = port
        self.sock = None
        self.running = False
        self.last_heartbeat = 0
        self.client_addr = None
        self.timeout_ms = 2000  # Stop if no command for 2s
    
    def start(self):
        """Start the UDP server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.setblocking(False)
        self.running = True
        print(f"UDP server listening on port {self.port}")
    
    def stop(self):
        """Stop the server."""
        self.running = False
        if self.sock:
            self.sock.close()
    
    def process_command(self, cmd):
        """Process a command string."""
        parts = cmd.strip().upper().split()
        if not parts:
            return "ERR: Empty command"
        
        action = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Movement commands
        if action == "FWD" or action == "FORWARD":
            speed = float(args[0]) if args else 1.0
            self.robot.forward(speed)
            return "OK: Forward"
        
        elif action == "BACK" or action == "BACKWARD":
            speed = float(args[0]) if args else 1.0
            self.robot.backward(speed)
            return "OK: Backward"
        
        elif action == "LEFT":
            speed = float(args[0]) if args else 1.0
            self.robot.left(speed)
            return "OK: Left"
        
        elif action == "RIGHT":
            speed = float(args[0]) if args else 1.0
            self.robot.right(speed)
            return "OK: Right"
        
        elif action == "STOP" or action == "HALT":
            self.robot.halt()
            return "OK: Stopped"
        
        # Poses
        elif action == "STAND":
            self.robot.stand()
            return "OK: Standing"
        
        elif action == "SIT":
            self.robot.sit()
            return "OK: Sitting"
        
        elif action == "CROUCH":
            self.robot.crouch()
            return "OK: Crouching"
        
        # Actions
        elif action == "WAVE":
            self.robot.wave()
            return "OK: Waving"
        
        elif action == "BOW":
            self.robot.bow()
            return "OK: Bowing"
        
        elif action == "SHAKE":
            self.robot.shake()
            return "OK: Shaking"
        
        elif action == "WIGGLE":
            self.robot.wiggle()
            return "OK: Wiggling"
        
        # Eye expressions
        elif action == "HAPPY":
            self.robot.happy()
            return "OK: Happy"
        
        elif action == "SAD":
            self.robot.sad()
            return "OK: Sad"
        
        elif action == "ANGRY":
            self.robot.angry()
            return "OK: Angry"
        
        elif action == "SLEEP":
            self.robot.sleep()
            return "OK: Sleeping"
        
        elif action == "WAKE":
            self.robot.wake()
            return "OK: Awake"
        
        # Direct servo control: SERVO <name> <angle>
        elif action == "SERVO":
            if len(args) >= 2:
                name = args[0]
                angle = int(args[1])
                self.robot.set_servo(name, angle)
                return f"OK: {name}={angle}"
            return "ERR: SERVO <name> <angle>"
        
        # Center all servos
        elif action == "CENTER":
            self.robot.center_all()
            return "OK: Centered"
        
        # Status request
        elif action == "STATUS" or action == "PING":
            return "OK: Ready"
        
        # Help
        elif action == "HELP":
            return "CMDS: FWD BACK LEFT RIGHT STOP STAND SIT WAVE BOW SHAKE WIGGLE HAPPY SAD SERVO CENTER"
        
        else:
            return f"ERR: Unknown '{action}'"
    
    def update(self):
        """Check for incoming commands. Call in main loop."""
        if not self.running:
            return
        
        try:
            data, addr = self.sock.recvfrom(256)
            self.client_addr = addr
            self.last_heartbeat = time.ticks_ms()
            
            cmd = data.decode('utf-8')
            response = self.process_command(cmd)
            
            # Send response
            self.sock.sendto(response.encode('utf-8'), addr)
            print(f"[{addr[0]}] {cmd.strip()} -> {response}")
            
        except OSError:
            pass  # No data available
        
        # Safety timeout
        if self.client_addr and self.last_heartbeat:
            if time.ticks_diff(time.ticks_ms(), self.last_heartbeat) > self.timeout_ms:
                print("Client timeout - stopping")
                self.robot.halt()
                self.last_heartbeat = 0


# Test
if __name__ == "__main__":
    from robot import Robot
    
    bot = Robot()
    bot.start()
    
    server = UDPServer(bot)
    server.start()
    
    print("Server running. Send UDP commands to port 5005")
    while True:
        server.update()
        bot.update()
        time.sleep_ms(10)
