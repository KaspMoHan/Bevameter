# config.py

import os

# -----------------------------------------------------------------------------
# Communication settings
# -----------------------------------------------------------------------------
# Choose 'serial' or 'tcp'
CONNECTION_TYPE = os.getenv('OPTA_CONN', 'serial')

# Serial settings
# ─────────────────────────────────────────────────────────────────────────────
# On Linux/macOS use '/dev/ttyUSB0', on Windows e.g. 'COM3'
SERIAL_PORT = os.getenv('OPTA_SERIAL_PORT', 'COM3')
BAUD_RATE   = int(os.getenv('OPTA_BAUD_RATE', '115200'))


# -----------------------------------------------------------------------------
# PID controller parameters
# -----------------------------------------------------------------------------
PID_KP = float(os.getenv('PID_KP', '1.0'))
PID_KI = float(os.getenv('PID_KI', '0.0'))
PID_KD = float(os.getenv('PID_KD', '0.0'))

# -----------------------------------------------------------------------------
# Rotation control parameters
# -----------------------------------------------------------------------------
ROTATION_DEG = float(os.getenv('ROTATION_DEG', '90.0'))
ROTATION_TIME = float(os.getenv('ROTATION_TIME', '30.0'))
CONTROL_FREQUENCY = float(os.getenv('CONTROL_FREQUENCY', '20.0'))

# -----------------------------------------------------------------------------
# Actuator speed limits (units/sec)
# -----------------------------------------------------------------------------
MIN_SPEED = float(os.getenv('MIN_SPEED', '-100.0'))
MAX_SPEED = float(os.getenv('MAX_SPEED', '100.0'))
