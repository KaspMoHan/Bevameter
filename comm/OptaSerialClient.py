import serial
import threading

class OptaSerialClient:
  
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.ser = None
        self._recv_thread = None
        self._running = False

        # User callback: set this to a function(line: str)
        self.on_message = None

    def connect(self):
        """Open the serial port and start reading."""
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self._running = True
        self._recv_thread = threading.Thread(
            target=self._read_loop,
            name="OptaSerialRecv",
            daemon=True
        )
        self._recv_thread.start()
        print(f"[OptaSerialClient] Connected on {self.port}@{self.baudrate}")

    def _read_loop(self):
        """Continuously read lines and invoke the callback."""
        while self._running:
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line and self.on_message:
                    self.on_message(line)
            except serial.SerialException as e:
                print(f"[OptaSerialClient] Serial error: {e}")
                break

    def send(self, cmd: str):
        """Send a line (adds '\\n')."""
        if not self.ser or not self.ser.is_open:
            raise ConnectionError("Serial port not open")
        self.ser.write((cmd.strip() + "\n").encode())

    def close(self):
        """Stop the thread and close port."""
        self._running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("[OptaSerialClient] Closed")
