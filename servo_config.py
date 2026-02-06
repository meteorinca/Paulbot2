# servo_config.py --- SERVO CONFIGURATION FILE
# ============================================
# This is the ONLY file you need to edit to adjust servo behavior!
#
# NAMING CONVENTION:
#   Femurs (move leg inward/outward, top-view):
#     R1 = Front Right femur   R2 = Back Right femur
#     L1 = Front Left femur    L2 = Back Left femur
#   Knees (lift foot off ground):
#     R3 = Front Right knee    R4 = Back Right knee
#     L3 = Front Left knee     L4 = Back Left knee

# ==========================
# PIN ASSIGNMENTS (ESP32)
# ==========================
# pins are wrong: right now if i do:
# trying to move L4 moves R3 (wrong dir)
# R4 moves L4 right dir
# R3 moved R4
# L3 moves L3 wrong dir

SERVO_PINS = {
    # Femurs
    "R2": 26,   # Front Right femur
    "L2": 33,   # Back Right femur
    "R1": 25,   # Front Left femur
    "L1": 32,   # Back Left femur
    # Knees
    "R4": 13,   # Front Right knee
    "L4": 27,   # Back Right knee
    "R3": 14,   # Front Left knee
    "L3": 12,   # Back Left knee
}

# ==========================
# SERVO DIRECTION (INVERSION)
# ==========================
# Set to True if servo moves OPPOSITE to expected direction.
# TEST EACH SERVO and flip this if needed!

SERVO_INVERTED = {
    "R1": False,
    "R2": False,
    "L1": True,
    "L2": True,
    "R3": False,
    "R4": True,
    "L3": True,
    "L4": False,
}

# ==========================
# ANGLE LIMITS (Min / Max)
# ==========================
# Wide limits for now - tighten after calibration

SERVO_LIMITS = {
    "R1": (0, 180),
    "R2": (0, 180),
    "L1": (0, 180),
    "L2": (0, 180),
    "R3": (0, 180),
    "R4": (0, 180),
    "L3": (0, 180),
    "L4": (0, 180),
}

# ==========================
# DEFAULT/CENTER POSITIONS
# ==========================
SERVO_CENTER = {
    "R1": 90,
    "R2": 90,
    "L1": 90,
    "L2": 90,
    "R3": 90,
    "R4": 90,
    "L3": 90,
    "L4": 90,
}

# ==========================
# SPEED CONFIGURATION
# ==========================
SERVO_SPEED = {
    "R1": 0.15,
    "R2": 0.15,
    "L1": 0.15,
    "L2": 0.15,
    "R3": 0.12,
    "R4": 0.12,
    "L3": 0.12,
    "L4": 0.12,
}

SPEED_MULTIPLIER = 1.0

# ==========================
# GAIT PARAMETERS
# ==========================
GAIT = {
    "STAND_FEMUR": 90,
    "STAND_KNEE": 180,
    "SPLAY_KNEE": 90,
    "STEP_LIFT": 110,
    "STEP_PLANT": 180,
    "STEP_FWD": 115,
    "STEP_BACK": 65,
}

# ==========================
# DESCRIPTIVE NAMES
# ==========================
SERVO_NAMES = {
    "R1": "Front Right Femur",
    "R2": "Back Right Femur",
    "L1": "Front Left Femur",
    "L2": "Back Left Femur",
    "R3": "Front Right Knee",
    "R4": "Back Right Knee",
    "L3": "Front Left Knee",
    "L4": "Back Left Knee",
}

# Groupings
FEMUR_SERVOS = ["R1", "R2", "L1", "L2"]
KNEE_SERVOS = ["R3", "R4", "L3", "L4"]
ALL_SERVOS = FEMUR_SERVOS + KNEE_SERVOS

LEGS = {
    "FR": ("R1", "R3"),
    "FL": ("L1", "L3"),
    "BR": ("R2", "R4"),
    "BL": ("L2", "L4"),
}

# ==========================
# I2C DISPLAY PINS
# ==========================
OLED_SCL_PIN = 22
OLED_SDA_PIN = 21
OLED_WIDTH = 128
OLED_HEIGHT = 64
