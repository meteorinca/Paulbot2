# Quadruped Robot Controller

ESP32-S3 MicroPython-based quadruped robot with WiFi control and OLED eye display.

## Hardware

- **MCU**: ESP32-S3
- **Servos**: 8x (4 femur + 4 knee)
- **Display**: 128x64 I2C OLED (SSD1306)
- **Power**: External servo power recommended

## Pin Configuration

| Servo | Pin | Function |
|-------|-----|----------|
| R1 | 25 | Front Right Femur |
| R2 | 26 | Back Right Femur |
| L1 | 32 | Front Left Femur |
| L2 | 33 | Back Left Femur |
| R3 | 14 | Front Right Knee |
| R4 | 13 | Back Right Knee |
| L3 | 12 | Front Left Knee |
| L4 | 27 | Back Left Knee |

| I2C | Pin |
|-----|-----|
| SCL | 22 |
| SDA | 21 |

## File Structure

```
├── main.py          # Entry point - WiFi + main loop
├── robot.py         # High-level robot orchestration
├── servos.py        # Servo control + PWM
├── display.py       # OLED eye animations
├── gaits.py         # Walking patterns + poses
├── udp_server.py    # Network command server
├── servo_config.py  # Pin and calibration settings
└── controller.py    # PC-side control script
```

## Quick Start

1. **Configure WiFi** in `main.py`:
   ```python
   WIFI_SSID = "YourNetwork"
   WIFI_PASS = "YourPassword"
   ```

2. **Upload files** to ESP32:
   ```bash
   # Using ampy, mpremote, or Thonny IDE
   mpremote cp *.py :
   ```

3. **Run**:
   ```bash
   mpremote run main.py
   # Or reset ESP32 for auto-start
   ```

4. **Control from PC**:
   ```bash
   python controller.py 192.168.1.xxx
   ```

## UDP Commands

| Command | Description |
|---------|-------------|
| `FWD [speed]` | Walk forward |
| `BACK [speed]` | Walk backward |
| `LEFT [speed]` | Turn left |
| `RIGHT [speed]` | Turn right |
| `STOP` | Stop walking |
| `STAND` | Stand pose |
| `SIT` | Sit pose |
| `WAVE` | Wave gesture |
| `BOW` | Bow gesture |
| `SHAKE` | Body shake |
| `WIGGLE` | Tail wiggle |
| `HAPPY` | Happy eyes |
| `SAD` | Sad eyes |
| `ANGRY` | Angry eyes |
| `SLEEP` | Sleep mode |
| `SERVO R1 90` | Direct servo control |
| `CENTER` | Center all servos |
| `PING` | Check connection |

## Calibration

Edit `servo_config.py`:

- `SERVO_INVERTED`: Flip direction if servo moves wrong way
- `SERVO_LIMITS`: Set safe angle ranges
- `SERVO_CENTER`: Adjust neutral positions
- `GAIT`: Tune walking parameters

## Future: Swarm Control

This robot is designed for swarm operation. Each robot:
- Has unique IP on the network
- Responds to same command protocol
- Can be controlled from a single web UI

Swarm controller coming soon!