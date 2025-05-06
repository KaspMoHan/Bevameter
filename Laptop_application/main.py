import sys
from PyQt5.QtWidgets import QApplication
from comm.OptaSerialClient import OptaSerialClient
from core.controller import Controller
from gui.main_window import MainWindow
import config
import pyduinocli  # ensure pyduinocli is available


def main():
    app = QApplication(sys.argv)

    # Optional serial client (uncommented)
    try:
        client = OptaSerialClient(
            port=config.SERIAL_PORT,
            baudrate=config.BAUD_RATE
        )
        client.connect()
        print(f"[OptaSerialClient] Connected on {config.SERIAL_PORT}@{config.BAUD_RATE}")

        # Upon successful serial connection, upload sketch via pyduinocli
        try:
            arduino = pyduinocli.Arduino()  # adjust path to arduino-cli binary if necessary
            boards = arduino.board.list().get('result', [])
            if boards:
                # Find board matching our serial port, or use first
                board = next(
                    (b for b in boards
                     if b.get('port', {}).get('address') == config.SERIAL_PORT),
                    boards[0]
                )
                port = board.get('port', {}).get('address')
                fqbn = board.get('matching_boards', [{}])[0].get('fqbn')
                sketch_path = 'core/UploadMe.cpp'
                print(f"[Pyduinocli] Uploading sketch '{sketch_path}' to {port} (FQBN={fqbn})")
                arduino.compile(fqbn=fqbn, sketch=sketch_path)
                arduino.upload(fqbn=fqbn, sketch=sketch_path, port=port)
                print("[Pyduinocli] Sketch uploaded successfully")
            else:
                print("[Pyduinocli] No Arduino boards detected for upload")
        except Exception as e:
            print(f"[Pyduinocli] Sketch upload failed: {e}")

    except Exception as e:
        print(f"[OptaSerialClient] Warning: could not connect ({e})")
        client = None

    # Initialize controller and GUI
    controller = Controller(interval=100)
    window = MainWindow(controller)
    window.serial_client = client

    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
