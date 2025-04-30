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
