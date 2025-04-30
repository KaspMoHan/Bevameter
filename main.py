import sys
from PyQt5.QtWidgets import QApplication
from comm.OptaSerialClient import OptaSerialClient
from core.controller import Controller
from gui.main_window import MainWindow
import config

def main():
    app = QApplication(sys.argv)

    # ——— Optional serial client (uncommented) ———
    try:
        client = OptaSerialClient(
            port=config.SERIAL_PORT,
            baudrate=config.BAUD_RATE
        )
        client.connect()
        print(f"[OptaSerialClient] Connected on {config.SERIAL_PORT}@{config.BAUD_RATE}")
    except Exception as e:
        print(f"[OptaSerialClient] Warning: could not connect ({e})")
        client = None

    # Core controller and GUI
    controller = Controller(interval=100)
    window = MainWindow(controller)
    # make serial client available for Emergency Stop
    window.serial_client = client

    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
