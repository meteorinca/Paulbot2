Excellent choice! For a PC/phone and ESP32-S3 on the same local router, you've got a solid setup for low-latency control. Here's an optimized architecture and code implementation:

## Recommended Architecture

**Mode:** Station (STA) to home router - most practical for your use case  
**Protocol:** UDP - best for low-latency control traffic  
**Packet Format:** Compact binary for minimum overhead

## Complete Implementation

### ESP32-S3 Side (Robot Controller)

```python
import network
import time
import socket
import struct
from machine import Pin, PWM

# ===== WiFi Connection =====
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=wlan.PM_NONE)  # Disable power saving for lower latency
    
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect("YOUR_SSID", "YOUR_PASSWORD")
        
        # Wait with timeout
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(0.5)
            timeout -= 1
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"Connected! IP: {ip}")
        return ip
    else:
        print("WiFi connection failed")
        return None

# ===== UDP Server Setup =====
class RobotController:
    def __init__(self):
        self.ip = connect_wifi()
        self.udp_port = 5005
        self.sock = None
        self.running = False
        
        # Motor control setup (adjust pins for your hardware)
        self.motor_left_pwm = PWM(Pin(18), freq=1000)
        self.motor_right_pwm = PWM(Pin(19), freq=1000)
        self.motor_left_dir = Pin(21, Pin.OUT)
        self.motor_right_dir = Pin(22, Pin.OUT)
        
        # Control variables
        self.left_speed = 0
        self.right_speed = 0
        self.deadband = 0.1  # Ignore very small commands
        
        # Telemetry
        self.telemetry_rate = 0  # Hz (0 = no telemetry)
        self.last_telemetry_time = 0
        
    def setup_udp(self):
        """Create non-blocking UDP socket"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', self.udp_port))
        self.sock.setblocking(False)
        print(f"UDP server listening on port {self.udp_port}")
    
    def parse_command(self, data):
        """
        Parse binary command packet (9 bytes total):
        Byte 0-1: Left motor speed (int16, -1000 to 1000)
        Byte 2-3: Right motor speed (int16, -1000 to 1000)
        Byte 4-5: Telemetry request rate (uint16, Hz)
        Byte 6-7: Sequence number (uint16, for loss detection)
        Byte 8: Flags (bit 0: enable motors, bit 1: emergency stop)
        """
        if len(data) != 9:
            return False
            
        left, right, telemetry_rate, seq, flags = struct.unpack('<hhHHB', data)
        
        # Apply deadband
        if abs(left) < 100:  # 10% deadband
            left = 0
        if abs(right) < 100:
            right = 0
        
        self.left_speed = left / 1000.0  # Convert to -1.0 to 1.0
        self.right_speed = right / 1000.0
        self.telemetry_rate = telemetry_rate
        
        # Process flags
        if flags & 0x02:  # Emergency stop
            self.left_speed = 0
            self.right_speed = 0
            
        return True
    
    def update_motors(self):
        """Convert normalized speeds to PWM and direction"""
        # Convert -1.0 to 1.0 range to PWM duty (0-1023)
        left_duty = int(abs(self.left_speed) * 1023)
        right_duty = int(abs(self.right_speed) * 1023)
        
        # Set direction pins
        self.motor_left_dir.value(1 if self.left_speed >= 0 else 0)
        self.motor_right_dir.value(1 if self.right_speed >= 0 else 0)
        
        # Apply PWM
        self.motor_left_pwm.duty(left_duty)
        self.motor_right_pwm.duty(right_duty)
    
    def get_telemetry(self):
        """
        Create telemetry packet (14 bytes):
        Byte 0-1: Left encoder count (int16)
        Byte 2-3: Right encoder count (int16)
        Byte 4-5: Battery voltage (uint16, mV)
        Byte 6-7: Left current (uint16, mA)
        Byte 8-9: Right current (uint16, mA)
        Byte 10-11: CPU temp (int16, °C * 10)
        Byte 12-13: Sequence echo (uint16)
        """
        # Replace with actual sensor readings
        left_encoder = 0
        right_encoder = 0
        battery_mv = 4200
        left_current = 0
        right_current = 0
        cpu_temp = int((time.ticks_cpu() // 10000) % 50)  # Fake temp
        
        return struct.pack('<hhHHHhh', 
                          left_encoder, right_encoder,
                          battery_mv, left_current, right_current,
                          cpu_temp, 0)
    
    def run(self):
        """Main control loop"""
        self.setup_udp()
        self.running = True
        
        seq_counter = 0
        packet_loss = 0
        last_seq = 0
        
        while self.running:
            # 1. Check for incoming commands
            try:
                data, addr = self.sock.recvfrom(64)
                if self.parse_command(data):
                    # Send telemetry if requested
                    if self.telemetry_rate > 0:
                        current_time = time.ticks_ms()
                        if time.ticks_diff(current_time, self.last_telemetry_time) > (1000 // self.telemetry_rate):
                            telemetry = self.get_telemetry()
                            self.sock.sendto(telemetry, addr)
                            self.last_telemetry_time = current_time
            except OSError:
                pass  # No data available
            
            # 2. Update motor outputs
            self.update_motors()
            
            # 3. Small delay to control loop rate (adjust as needed)
            time.sleep_ms(5)  # ~200 Hz control loop

# ===== Main Execution =====
if __name__ == "__main__":
    robot = RobotController()
    if robot.ip:
        robot.run()
```

### PC Side (Controller - Python)

```python
import socket
import struct
import time
import threading
from inputs import get_gamepad  # pip install inputs

class RobotRemote:
    def __init__(self, robot_ip="192.168.1.100", port=5005):
        self.robot_ip = robot_ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.left_speed = 0
        self.right_speed = 0
        self.seq = 0
        self.running = False
        
        # Telemetry
        self.last_telemetry = None
        self.telem_lock = threading.Lock()
        
    def create_command(self, left, right, enable=True, telemetry_rate=20):
        """Create 9-byte command packet"""
        flags = 0x01 if enable else 0x00
        self.seq = (self.seq + 1) % 65536
        
        return struct.pack('<hhHHB',
                          int(left * 1000),  # -1000 to 1000
                          int(right * 1000),
                          telemetry_rate,
                          self.seq,
                          flags)
    
    def send_command(self, left, right):
        """Send command to robot"""
        cmd = self.create_command(left, right)
        self.sock.sendto(cmd, (self.robot_ip, self.port))
    
    def telemetry_thread(self):
        """Receive telemetry in background"""
        self.sock.bind(('0.0.0.0', self.port + 1))  # Different port for receiving
        
        while self.running:
            try:
                data, _ = self.sock.recvfrom(64)
                if len(data) == 14:
                    with self.telem_lock:
                        self.last_telemetry = struct.unpack('<hhHHHhh', data)
            except:
                pass
    
    def gamepad_control(self):
        """Use gamepad for control (Xbox/PS4 controller)"""
        print("Gamepad control active. Use left stick for movement.")
        
        telemetry_thread = threading.Thread(target=self.telemetry_thread)
        telemetry_thread.daemon = True
        self.running = True
        telemetry_thread.start()
        
        try:
            while True:
                events = get_gamepad()
                for event in events:
                    if event.code == "ABS_Y":  # Left stick Y axis
                        # Convert -32768 to 32767 to -1.0 to 1.0
                        left = -event.state / 32768.0
                        right = left  # Tank drive
                        self.send_command(left, right)
                        
                    elif event.code == "ABS_X":  # Left stick X for steering
                        # Mix steering (arcade drive)
                        forward = self.left_speed
                        turn = event.state / 32768.0
                        self.left_speed = forward + turn
                        self.right_speed = forward - turn
                        self.send_command(self.left_speed, self.right_speed)
                        
                    elif event.code == "BTN_SOUTH":  # A button on Xbox
                        if event.state == 1:
                            print("Emergency stop!")
                            self.send_command(0, 0)
                
                # Display telemetry
                if self.last_telemetry:
                    print(f"Battery: {self.last_telemetry[2]/1000:.2f}V | "
                          f"Temp: {self.last_telemetry[5]/10:.1f}C")
                    
                time.sleep(0.01)  # ~100 Hz update rate
                
        except KeyboardInterrupt:
            print("\nStopping...")
            self.send_command(0, 0)  # Send stop command
            self.running = False

# Alternative: Keyboard control
def keyboard_control(remote):
    """Simple keyboard control with WASD"""
    import sys
    import select
    
    print("WASD control (Q to quit)")
    
    speed = 0.5
    left = 0
    right = 0
    
    while True:
        # Non-blocking keyboard input
        if select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1).lower()
            
            if key == 'w':
                left = speed
                right = speed
            elif key == 's':
                left = -speed
                right = -speed
            elif key == 'a':
                left = -speed
                right = speed
            elif key == 'd':
                left = speed
                right = -speed
            elif key == ' ':
                left = 0
                right = 0
            elif key == 'q':
                break
            
            remote.send_command(left, right)
        
        time.sleep(0.05)

if __name__ == "__main__":
    # Replace with your robot's IP
    remote = RobotRemote(robot_ip="192.168.1.100")
    
    # Choose control method:
    # remote.gamepad_control()  # For gamepad
    # keyboard_control(remote)  # For keyboard
```

## Web/Phone Controller (Simple HTML/JS)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Robot Controller</title>
    <style>
        body { margin: 0; padding: 20px; }
        .joystick {
            width: 200px;
            height: 200px;
            background: #ddd;
            border-radius: 50%;
            position: relative;
            margin: 20px auto;
            touch-action: none;
        }
        .handle {
            width: 60px;
            height: 60px;
            background: #444;
            border-radius: 50%;
            position: absolute;
            top: 70px;
            left: 70px;
        }
    </style>
</head>
<body>
    <h2>Robot Controller</h2>
    <div class="joystick" id="joystick">
        <div class="handle" id="handle"></div>
    </div>
    <div>Left: <span id="left">0</span>%</div>
    <div>Right: <span id="right">0</span>%</div>
    
    <script>
        const ROBOT_IP = "192.168.1.100";
        const PORT = 5005;
        let socket = null;
        let seq = 0;
        
        function connect() {
            // Create WebSocket connection to a local proxy
            // Or use UDP via WebRTC with a local server
            console.log("Note: Browser needs a WebSocket proxy to UDP");
            alert("Run: python websocket_proxy.py on your PC first");
        }
        
        function sendCommand(left, right) {
            // Create binary packet
            const buffer = new ArrayBuffer(9);
            const view = new DataView(buffer);
            
            view.setInt16(0, Math.round(left * 1000), true); // Little-endian
            view.setInt16(2, Math.round(right * 1000), true);
            view.setUint16(4, 10, true); // Telemetry rate (10 Hz)
            view.setUint16(6, seq++, true);
            view.setUint8(8, 0x01); // Flags
            
            // Send via WebSocket to proxy
            if (socket) {
                socket.send(buffer);
            }
            
            document.getElementById('left').textContent = Math.round(left * 100);
            document.getElementById('right').textContent = Math.round(right * 100);
        }
        
        // Joystick control
        const joystick = document.getElementById('joystick');
        const handle = document.getElementById('handle');
        let dragging = false;
        
        function updateJoystick(x, y) {
            const rect = joystick.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Convert to -1.0 to 1.0
            const normX = (x - centerX) / centerX;
            const normY = (y - centerY) / centerY;
            
            // Arcade drive mixing
            const max = Math.max(Math.abs(normX), Math.abs(normY));
            let left = normY + normX;
            let right = normY - normX;
            
            // Scale to keep within -1.0 to 1.0
            const scale = max > 1 ? 1 / max : 1;
            left *= scale;
            right *= scale;
            
            sendCommand(left, right);
            
            // Visual feedback
            handle.style.left = (centerX + normX * centerX - 30) + 'px';
            handle.style.top = (centerY + normY * centerY - 30) + 'px';
        }
        
        joystick.addEventListener('mousedown', (e) => {
            dragging = true;
            updateJoystick(e.offsetX, e.offsetY);
        });
        
        joystick.addEventListener('mousemove', (e) => {
            if (dragging) updateJoystick(e.offsetX, e.offsetY);
        });
        
        document.addEventListener('mouseup', () => {
            dragging = false;
            handle.style.left = '70px';
            handle.style.top = '70px';
            sendCommand(0, 0);
        });
        
        // Touch support
        joystick.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const rect = joystick.getBoundingClientRect();
            updateJoystick(touch.clientX - rect.left, touch.clientY - rect.top);
        });
        
        joystick.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const rect = joystick.getBoundingClientRect();
            updateJoystick(touch.clientX - rect.left, touch.clientY - rect.top);
        });
        
        joystick.addEventListener('touchend', () => {
            handle.style.left = '70px';
            handle.style.top = '70px';
            sendCommand(0, 0);
        });
    </script>
</body>
</html>
```

## WebSocket Proxy (PC side, for browser control)

```python
# websocket_proxy.py
import asyncio
import websockets
import socket
import struct

class WebSocketProxy:
    def __init__(self, robot_ip="192.168.1.100", robot_port=5005):
        self.robot_addr = (robot_ip, robot_port)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    async def handle_client(self, websocket, path):
        print(f"Client connected: {websocket.remote_address}")
        try:
            async for message in websocket:
                # Forward binary WebSocket message as UDP to robot
                self.udp_sock.sendto(message, self.robot_addr)
                
                # Optional: forward telemetry back to client
                # (requires robot to send telemetry to this proxy)
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
    
    async def start(self, port=8765):
        print(f"WebSocket proxy running on ws://0.0.0.0:{port}")
        print(f"Forwarding to UDP {self.robot_addr}")
        async with websockets.serve(self.handle_client, "0.0.0.0", port):
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    proxy = WebSocketProxy()
    asyncio.run(proxy.start())
```

## Key Optimization Tips:

1. **Network Settings:**
   ```python
   # On ESP32, set WiFi to maximum performance
   wlan.config(pm=network.WLAN.PM_NONE)  # No power saving
   ```

2. **Socket Optimization:**
   ```python
   sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   ```

3. **Control Loop Timing:**
   - Use `time.ticks_ms()` for precise timing
   - Target 50-100Hz control rate maximum
   - Keep loop iterations under 10ms

4. **Packet Loss Handling:**
   - Sequence numbers in packets
   - Timeout detection (if no packet for X ms, stop motors)
   - Exponential moving average for smoothing

## Expected Performance:
- **Latency:** 5-30ms on good local network
- **Update Rate:** 50-200Hz achievable
- **Reliability:** Good for local network, add sequence numbers for loss detection

This setup gives you flexible control options (Python script, gamepad, or web interface) with minimal latency. The binary UDP protocol ensures fast processing on the ESP32.