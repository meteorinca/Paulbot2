

import network
import time

# WiFi Configuration - EDIT THESE!
WIFI_SSID = "PUTWIFINAME"
WIFI_PASS = "PUTWIFIPASSWORD"
UDP_PORT = 5005


def connect_wifi():
    """Connect to WiFi network."""
    wlan = network.WLAN(network.STA_IF)
    
    # Reset first
    wlan.active(False)
    time.sleep(1)
    
    try:
        wlan.active(True)
        print("WiFi active")
        time.sleep(3)  # ESP32-S3 needs this settle time
    except:
        print("WiFi activation failed")
        return None
    
    if not wlan.active():
        print("WiFi not started!")
        return None
        
    # Your original code from here
    try:
        wlan.config(pm=wlan.PM_NONE)
    except:
        pass
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"Already connected: {ip}")
        return ip
    
    print(f"Connecting to {WIFI_SSID}...")
    wlan.connect(WIFI_SSID, WIFI_PASS)
    
    timeout = 40
    while not wlan.isconnected() and timeout > 0:
        time.sleep(0.5)
        timeout -= 1
        print(".", end="")
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\nConnected! IP: {ip}")
        return ip
    else:
        print("\nWiFi connection failed!")
        return None





def main():
    """Main entry point."""
    print("=" * 40)
    print("  QUADRUPED ROBOT CONTROLLER")
    print("=" * 40)
    
    # Connect to WiFi
    ip = connect_wifi()
    
    # Initialize robot
    from robot import Robot
    from udp_server import UDPServer
    
    bot = Robot()
    bot.start()
    
    # Show happy on startup
    bot.eyes.set_animation("happy", 2000)
    
    if ip:
        # Start UDP server
        server = UDPServer(bot, UDP_PORT)
        server.start()
        print(f"\nSend commands to {ip}:{UDP_PORT}")
        print("Commands: FWD, BACK, LEFT, RIGHT, STOP")
        print("          STAND, SIT, WAVE, BOW, SHAKE")
        print("          HAPPY, SAD, ANGRY, SLEEP")
        print("          SERVO <name> <angle>, CENTER")
        
        # Main loop with server
        while True:
            try:
                server.update()
                bot.update()
                time.sleep_ms(10)
            except KeyboardInterrupt:
                print("\nShutting down...")
                bot.stop()
                server.stop()
                break
    else:
        # Offline mode - just run demo
        print("\nRunning in offline mode...")
        print("Demo: Wave, then idle")
        
        bot.wave()
        for _ in range(150):
            bot.update()
            time.sleep_ms(20)
        
        bot.stand()
        
        # Keep updating eyes
        while True:
            try:
                bot.update()
                time.sleep_ms(20)
            except KeyboardInterrupt:
                bot.stop()
                break


# Auto-run when imported
if __name__ == "__main__":
    main()

