# SwarmWebAPP Developer Guide

> **Complete Technical Reference for Building the Quadruped Robot Swarm Control System**
> 
> Last Updated: February 2026

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Robot Architecture](#robot-architecture)
3. [Communication Protocol](#communication-protocol)
4. [Command Reference](#command-reference)
5. [Robot State & Capabilities](#robot-state--capabilities)
6. [Network Topology](#network-topology)
7. [Integration Examples](#integration-examples)
8. [Swarm Considerations](#swarm-considerations)
9. [Future Roadmap](#future-roadmap)

---

## System Overview

### What You're Building

A web application to control **multiple quadruped robots** simultaneously from a single interface. Each robot:
- Runs MicroPython on an ESP32-S3
- Connects to WiFi and gets a unique IP
- Listens for UDP commands on port 5005
- Has 8 servos (4 legs × 2 joints each)
- Has a 128×64 OLED display for "eyes"
- Responds to text-based commands

### Current State

| Component | Status | Notes |
|-----------|--------|-------|
| ESP32 firmware | ✅ Complete | All .py files in this folder |
| UDP protocol | ✅ Complete | Text commands, text responses |
| Single robot control | ✅ Complete | web_controller.html + udp_proxy.py |
| Swarm webapp | 🔧 TODO | **Your mission** |

---

## Robot Architecture

### Hardware Per Robot

```
┌────────────────────────────────────────────┐
│              ESP32-S3 MCU                  │
├────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  WiFi    │  │  8 PWM   │  │   I2C    │  │
│  │  Radio   │  │  Outputs │  │   Bus    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼─────────────┼─────────────┼────────┘
        │             │             │
        ▼             ▼             ▼
    ┌───────┐    ┌─────────┐   ┌─────────┐
    │Network│    │8 Servos │   │  OLED   │
    │  UDP  │    │ SG90/   │   │ 128×64  │
    │ :5005 │    │ MG90S   │   │ Display │
    └───────┘    └─────────┘   └─────────┘
```

### Software Stack (on Robot)

```
main.py                 ← Entry point, WiFi, main loop
    ├── robot.py        ← High-level orchestration
    │   ├── servos.py   ← PWM servo control
    │   ├── display.py  ← OLED eye animations
    │   └── gaits.py    ← Walking patterns
    └── udp_server.py   ← Network command handler
    
servo_config.py         ← Pin assignments, calibration
```

### Servo Layout

```
      FRONT
   ┌─────────┐
   │ L1   R1 │  ← Front femurs (horizontal swing)
   │ L3   R3 │  ← Front knees (vertical lift)
   │         │
   │ L2   R2 │  ← Back femurs
   │ L4   R4 │  ← Back knees
   └─────────┘
      BACK

Leg Names:
  FL = Front Left  (L1 femur, L3 knee)
  FR = Front Right (R1 femur, R3 knee)
  BL = Back Left   (L2 femur, L4 knee)
  BR = Back Right  (R2 femur, R4 knee)
```

### Pin Mapping

| Servo | GPIO | Description |
|-------|------|-------------|
| R1 | 25 | Front Right Femur |
| R2 | 26 | Back Right Femur |
| L1 | 32 | Front Left Femur |
| L2 | 33 | Back Left Femur |
| R3 | 14 | Front Right Knee |
| R4 | 13 | Back Right Knee |
| L3 | 12 | Front Left Knee |
| L4 | 27 | Back Left Knee |
| OLED SCL | 22 | I2C Clock |
| OLED SDA | 21 | I2C Data |

---

## Communication Protocol

### Transport Layer

| Property | Value |
|----------|-------|
| Protocol | UDP |
| Port | 5005 |
| Encoding | UTF-8 text |
| Max packet size | 256 bytes |
| Response timeout | 2 seconds |
| Safety timeout | 2 seconds (robot stops if no commands) |

### Request Format

```
COMMAND [ARG1] [ARG2] ...
```

- Commands are **case-insensitive**
- Arguments are **space-separated**
- No delimiter needed at end

### Response Format

```
OK: <description>
```
or
```
ERR: <error message>
```

### Example Exchange

```
Client → Robot:  "FWD 0.8"
Robot → Client:  "OK: Forward"

Client → Robot:  "SERVO R1 120"
Robot → Client:  "OK: R1=120"

Client → Robot:  "BLAH"
Robot → Client:  "ERR: Unknown 'BLAH'"
```

---

## Command Reference

### Movement Commands

| Command | Arguments | Description | Response |
|---------|-----------|-------------|----------|
| `FWD` | `[speed]` | Walk forward | `OK: Forward` |
| `FORWARD` | `[speed]` | Alias for FWD | `OK: Forward` |
| `BACK` | `[speed]` | Walk backward | `OK: Backward` |
| `BACKWARD` | `[speed]` | Alias for BACK | `OK: Backward` |
| `LEFT` | `[speed]` | Turn left while walking | `OK: Left` |
| `RIGHT` | `[speed]` | Turn right while walking | `OK: Right` |
| `STOP` | - | Stop all movement | `OK: Stopped` |
| `HALT` | - | Alias for STOP | `OK: Stopped` |

**Speed**: Float from 0.0 to 2.0 (default: 1.0)

### Pose Commands

| Command | Description | Response |
|---------|-------------|----------|
| `STAND` | Standing pose | `OK: Standing` |
| `SIT` | Sitting pose | `OK: Sitting` |
| `CROUCH` | Low crouch | `OK: Crouching` |
| `CENTER` | All servos to 90° | `OK: Centered` |

### Action Commands

| Command | Description | Duration | Response |
|---------|-------------|----------|----------|
| `WAVE` | Wave front right leg | ~1.5s | `OK: Waving` |
| `BOW` | Bow gesture | ~1.5s | `OK: Bowing` |
| `SHAKE` | Body shake | ~1s | `OK: Shaking` |
| `WIGGLE` | Wiggle back end | ~0.8s | `OK: Wiggling` |

### Eye Expression Commands

| Command | Description | Duration | Response |
|---------|-------------|----------|----------|
| `HAPPY` | Happy eyes (^_^) | 2s | `OK: Happy` |
| `SAD` | Sad eyes | 2s | `OK: Sad` |
| `ANGRY` | Angry eyes | 2s | `OK: Angry` |
| `SLEEP` | Sleeping (indefinite) | Until changed | `OK: Sleeping` |
| `WAKE` | Surprised/awake | 0.5s | `OK: Awake` |

### Direct Servo Control

| Command | Arguments | Description | Response |
|---------|-----------|-------------|----------|
| `SERVO` | `<name> <angle>` | Set servo angle | `OK: <name>=<angle>` |

**Name**: R1, R2, L1, L2, R3, R4, L3, L4  
**Angle**: 0-180 degrees

Example: `SERVO R1 120` → `OK: R1=120`

### System Commands

| Command | Description | Response |
|---------|-------------|----------|
| `PING` | Check connection | `OK: Ready` |
| `STATUS` | Alias for PING | `OK: Ready` |
| `HELP` | List commands | `CMDS: FWD BACK...` |

---

## Robot State & Capabilities

### Eye Animations (15 types)

```python
ANIMATIONS = [
    "idle",        # Default, with auto-blink
    "blink",       # Single blink
    "look_left",   # Pupils look left
    "look_right",  # Pupils look right
    "look_up",     # Pupils look up
    "look_down",   # Pupils look down
    "happy",       # ^_^ curved eyes
    "sad",         # Droopy eyes
    "angry",       # Angled brows
    "surprised",   # Wide eyes
    "sleep",       # Closed with Z's
    "wink",        # One eye closed
    "heart",       # Heart-shaped eyes
    "dizzy",       # Spiral eyes
    "squint",      # Partially closed
]
```

### Poses

```python
POSES = {
    "neutral":  # All servos at 90°
    "stand":    # Standing position, knees extended
    "sit":      # Knees bent down
    "tall":     # Maximum extension
    "crouch":   # Low stance, ready to pounce
}
```

### Walking Gait

Uses **tripod gait** (alternating diagonal pairs):
- Group A: Front-Right + Back-Left
- Group B: Front-Left + Back-Right

One group lifts and swings while the other supports.

---

## Network Topology

### Single Robot

```
┌──────────┐         ┌──────────┐
│   PC     │  WiFi   │  Robot   │
│ Browser  │◄───────►│ ESP32-S3 │
│          │  UDP    │ :5005    │
└──────────┘         └──────────┘
```

### Swarm (Your Target)

```
                    ┌──────────┐
                    │ Robot 1  │
                    │ 192.168. │
              ┌────►│ 1.101    │
              │     └──────────┘
┌──────────┐  │     ┌──────────┐
│  Swarm   │  │     │ Robot 2  │
│  WebApp  │──┼────►│ 192.168. │
│          │  │     │ 1.102    │
└──────────┘  │     └──────────┘
              │     ┌──────────┐
              │     │ Robot 3  │
              └────►│ 192.168. │
                    │ 1.103    │
                    └──────────┘
```

### Browser Limitation

⚠️ **Browsers cannot send UDP directly!**

You need one of:

1. **HTTP→UDP Proxy** (current solution)
   - Run `udp_proxy.py` on local PC
   - Web app sends HTTP to proxy
   - Proxy forwards as UDP

2. **WebSocket Server on Robot** (requires firmware update)
   - Add WebSocket support to ESP32
   - Browser connects directly via WS

3. **Backend Server** (recommended for swarm)
   - Node.js/Python server with DB
   - Handles all robot communication
   - Web frontend talks to backend via REST/WS

---

## Integration Examples

### Python (Direct UDP)

```python
import socket

def send_command(ip, cmd, port=5005, timeout=2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    sock.sendto(cmd.encode(), (ip, port))
    try:
        data, _ = sock.recvfrom(256)
        return data.decode()
    except socket.timeout:
        return None

# Usage
response = send_command("192.168.1.100", "wave")
print(response)  # "OK: Waving"
```

### JavaScript (via Proxy)

```javascript
async function sendCommand(robotIp, cmd) {
    const proxyUrl = 'http://localhost:8080';
    const url = `${proxyUrl}/send?ip=${robotIp}&cmd=${encodeURIComponent(cmd)}`;
    
    const response = await fetch(url);
    return await response.text();
}

// Usage
const result = await sendCommand('192.168.1.100', 'happy');
console.log(result);  // "OK: Happy"
```

### Batch Command (Multiple Robots)

```javascript
async function swarmCommand(robotIps, cmd) {
    const promises = robotIps.map(ip => sendCommand(ip, cmd));
    const results = await Promise.all(promises);
    return robotIps.map((ip, i) => ({ ip, result: results[i] }));
}

// All robots wave at once!
const robots = ['192.168.1.101', '192.168.1.102', '192.168.1.103'];
const results = await swarmCommand(robots, 'wave');
```

---

## Swarm Considerations

### Robot Discovery

Options for finding robots on network:

1. **Static IP list** - Configure manually
2. **mDNS** - Robots advertise as `robot-001.local`
3. **Broadcast scan** - Send ping to broadcast address
4. **Registration** - Robots call home to server on boot

### Robot Identification

Each robot should have a unique ID. Options:

1. **MAC address** - Built-in, unique
2. **Assigned name** - Store in config file
3. **IP-based** - Last octet as ID

### Synchronized Commands

For coordinated movements:

```javascript
// Sequential (one after another)
for (const ip of robots) {
    await sendCommand(ip, 'wave');
    await delay(500);
}

// Parallel (all at once)
await Promise.all(robots.map(ip => sendCommand(ip, 'wave')));

// Choreographed
const choreography = [
    { delay: 0, robots: [0, 2], cmd: 'wave' },
    { delay: 500, robots: [1, 3], cmd: 'bow' },
    { delay: 1000, robots: 'all', cmd: 'happy' },
];
```

### Latency Considerations

- Local WiFi UDP latency: 5-30ms typical
- Browser→Proxy→Robot adds ~10-20ms
- For synchronized moves, may need timing compensation

### State Management

Track each robot's state:

```javascript
const robots = {
    'robot-001': {
        ip: '192.168.1.101',
        status: 'connected',  // connected, disconnected, error
        lastSeen: Date.now(),
        pose: 'stand',
        walking: false,
        expression: 'idle',
    },
    // ...
};
```

---

## Future Roadmap

### Planned Features (implement as needed)

| Feature | Priority | Notes |
|---------|----------|-------|
| Robot naming | High | Store name in robot config |
| Battery status | High | Need ADC reading on robot |
| Video streaming | Medium | ESP32-CAM integration |
| Position feedback | Medium | Encoder or IMU |
| Formation control | Medium | Relative positioning |
| Audio output | Low | Buzzer or I2S speaker |
| Sensor array | Low | Ultrasonic, IR, etc. |

### Protocol Extensions

When adding features, follow this pattern:

```
NEW_COMMAND [args]  →  OK: result
                   →  ERR: reason
```

### Firmware Updates

To add robot-side features:
1. Modify relevant .py file
2. Test on single robot
3. Update this document
4. Deploy to swarm

---

## Files Reference

| File | Purpose | Modify When |
|------|---------|-------------|
| `main.py` | Entry point, WiFi | Changing WiFi, startup |
| `robot.py` | Command orchestration | Adding high-level commands |
| `servos.py` | Servo control | Changing PWM, smoothing |
| `display.py` | Eye animations | Adding expressions |
| `gaits.py` | Walking patterns | Adding movements |
| `udp_server.py` | Network commands | Adding commands |
| `servo_config.py` | Hardware config | Calibration |
| `udp_proxy.py` | Browser bridge | Proxy features |
| `web_controller.html` | Basic UI | Reference only |

---

## Quick Test Checklist

Before developing swarm features:

- [ ] Robot boots and shows IP
- [ ] Can ping robot from PC: `python controller.py <ip>`
- [ ] Proxy works: `python udp_proxy.py`
- [ ] Web controller connects
- [ ] Movement commands work
- [ ] Expressions display correctly
- [ ] Multiple robots can coexist on network

---

## Contact & Resources

- **Robot firmware**: This folder (`*.py` files)
- **Hardware docs**: ESP32-S3 datasheet, SG90 servo specs
- **MicroPython**: https://docs.micropython.org

---

*Document maintained by the robotics team. Update as features are added.*
