# udp_proxy.py - HTTP to UDP Proxy for Web Controller
# ====================================================
# Bridges web browsers (HTTP) to robot (UDP)
# Run this on your PC alongside the web controller

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socket
import json
import time
import threading

UDP_PORT = 5005
HTTP_PORT = 8080
TIMEOUT = 2.0
HEARTBEAT_INTERVAL = 5.0  # seconds between heartbeat checks

# Global state for connection tracking
connection_state = {
    'last_successful_ip': None,
    'last_ping_time': None,
    'is_connected': False,
    'latency_ms': None,
    'total_commands': 0,
    'failed_commands': 0
}


class ProxyHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests and forward to robot via UDP."""
    
    def do_GET(self):
        # Parse URL
        parsed = urlparse(self.path)
        
        if parsed.path == '/send':
            params = parse_qs(parsed.query)
            robot_ip = params.get('ip', [''])[0]
            cmd = params.get('cmd', [''])[0]
            
            if not robot_ip or not cmd:
                self.send_error(400, 'Missing ip or cmd parameter')
                return
            
            # Track command
            connection_state['total_commands'] += 1
            
            # Send UDP and get response
            start_time = time.time()
            response = self.send_udp(robot_ip, cmd)
            latency = int((time.time() - start_time) * 1000)
            
            # Update connection state
            if 'TIMEOUT' not in response and 'ERROR' not in response:
                connection_state['is_connected'] = True
                connection_state['last_successful_ip'] = robot_ip
                connection_state['last_ping_time'] = time.time()
                connection_state['latency_ms'] = latency
            else:
                connection_state['failed_commands'] += 1
                if connection_state['last_successful_ip'] == robot_ip:
                    connection_state['is_connected'] = False
            
            # Send HTTP response with CORS
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = {
                'response': response,
                'latency_ms': latency,
                'connected': 'TIMEOUT' not in response and 'ERROR' not in response
            }
            self.wfile.write(json.dumps(result).encode())
        
        elif parsed.path == '/status':
            # Return connection status
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            status = {
                'proxy_running': True,
                'connected': connection_state['is_connected'],
                'last_ip': connection_state['last_successful_ip'],
                'latency_ms': connection_state['latency_ms'],
                'total_commands': connection_state['total_commands'],
                'failed_commands': connection_state['failed_commands'],
                'uptime': time.time()
            }
            self.wfile.write(json.dumps(status).encode())
        
        elif parsed.path == '/ping':
            # Quick ping to check if robot is reachable
            params = parse_qs(parsed.query)
            robot_ip = params.get('ip', [''])[0]
            
            if not robot_ip:
                self.send_error(400, 'Missing ip parameter')
                return
            
            start_time = time.time()
            response = self.send_udp(robot_ip, 'ping')
            latency = int((time.time() - start_time) * 1000)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = {
                'reachable': 'OK' in response,
                'response': response,
                'latency_ms': latency
            }
            self.wfile.write(json.dumps(result).encode())
            
        elif parsed.path == '/':
            # Serve info page with enhanced status
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            status_class = 'connected' if connection_state['is_connected'] else 'disconnected'
            self.wfile.write(f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>UDP Proxy Status</title>
                    <style>
                        body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #1a1a2e; color: #fff; padding: 40px; }}
                        h1 {{ color: #00d4ff; }}
                        .status {{ padding: 20px; background: rgba(255,255,255,0.05); border-radius: 12px; margin: 20px 0; }}
                        .connected {{ border-left: 4px solid #00e676; }}
                        .disconnected {{ border-left: 4px solid #ff5252; }}
                        .stat {{ margin: 10px 0; }}
                        .label {{ color: rgba(255,255,255,0.6); }}
                        code {{ background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 4px; }}
                    </style>
                </head>
                <body>
                    <h1>🤖 UDP Proxy Running</h1>
                    <div class="status {status_class}">
                        <div class="stat"><span class="label">Status:</span> {'Connected' if connection_state['is_connected'] else 'Disconnected'}</div>
                        <div class="stat"><span class="label">Last Robot IP:</span> {connection_state['last_successful_ip'] or 'None'}</div>
                        <div class="stat"><span class="label">Latency:</span> {connection_state['latency_ms'] or '---'}ms</div>
                        <div class="stat"><span class="label">Commands Sent:</span> {connection_state['total_commands']}</div>
                        <div class="stat"><span class="label">Failed Commands:</span> {connection_state['failed_commands']}</div>
                    </div>
                    <h2>API Endpoints</h2>
                    <ul>
                        <li><code>/send?ip=ROBOT_IP&cmd=COMMAND</code> - Send command to robot</li>
                        <li><code>/ping?ip=ROBOT_IP</code> - Check if robot is reachable</li>
                        <li><code>/status</code> - Get proxy status (JSON)</li>
                    </ul>
                    <p style="color: rgba(255,255,255,0.4); margin-top: 40px;">
                        Open <code>web_controller.html</code> in your browser to control the robot.
                    </p>
                    <script>
                        // Auto-refresh every 5 seconds
                        setTimeout(() => location.reload(), 5000);
                    </script>
                </body>
                </html>
            '''.encode())
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    
    def send_udp(self, robot_ip, cmd):
        """Send UDP command to robot and get response."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(TIMEOUT)
            sock.sendto(cmd.encode(), (robot_ip, UDP_PORT))
            
            data, _ = sock.recvfrom(256)
            sock.close()
            return data.decode()
        except socket.timeout:
            return "TIMEOUT"
        except Exception as e:
            return f"ERROR: {e}"
    
    def log_message(self, format, *args):
        """Custom logging with timestamps."""
        timestamp = time.strftime('%H:%M:%S')
        method = args[0].split()[0] if args else ''
        path = args[0].split()[1] if args and len(args[0].split()) > 1 else ''
        status = args[1] if len(args) > 1 else ''
        
        # Color coding for terminal
        if '/send' in path:
            print(f"[{timestamp}] 📤 {method} {path} -> {status}")
        elif '/ping' in path:
            print(f"[{timestamp}] 🔍 {method} {path} -> {status}")
        elif '/status' in path:
            print(f"[{timestamp}] 📊 Status check")
        else:
            print(f"[{timestamp}] {args[0]}")


def main():
    print("=" * 55)
    print("  🤖 UDP PROXY FOR QUADRUPED ROBOT - ENHANCED")
    print("=" * 55)
    print(f"\n📡 HTTP server: http://localhost:{HTTP_PORT}")
    print(f"📤 Forwarding to UDP port: {UDP_PORT}")
    print(f"⏱️  Command timeout: {TIMEOUT}s")
    print("\n📋 Endpoints:")
    print(f"   • /send?ip=IP&cmd=CMD  - Send command")
    print(f"   • /ping?ip=IP          - Check connection")
    print(f"   • /status              - Proxy status (JSON)")
    print(f"   • /                    - Status page (HTML)")
    print("\n🌐 Open web_controller.html in your browser")
    print("⌨️  Press Ctrl+C to stop\n")
    print("-" * 55)
    
    server = HTTPServer(('0.0.0.0', HTTP_PORT), ProxyHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        print(f"   Total commands: {connection_state['total_commands']}")
        print(f"   Failed commands: {connection_state['failed_commands']}")
        server.shutdown()


if __name__ == "__main__":
    main()
