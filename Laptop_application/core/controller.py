from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from enum import Enum, auto
import math, random
from core.data_logger import DataLogger

class State(Enum):
    PRESTART = auto()
    GROUSERTEST = auto()
    RUBBERTEST = auto()
    LOADTEST = auto()
    PAUSED = auto()

class Controller(QObject):
    data_updated = pyqtSignal(list)    # [t, v1, v2, v3]
    state_changed = pyqtSignal(State)
    log_message = pyqtSignal(str)      # messages for GUI command window

    def __init__(self, interval: int = 100):
        super().__init__()
        self.interval = interval
        self.timer = QTimer(self)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self._on_timeout)

        self.state = State.PRESTART
        self._sequence = []
        self._last_test = None
        self.t = 0.0
        self.logger = None

        # Handler maps
        self._enter_handlers = {
            State.PRESTART: self._enter_prestart,
            State.GROUSERTEST: self._enter_grouser,
            State.RUBBERTEST: self._enter_rubber,
            State.LOADTEST: self._enter_load,
            State.PAUSED: self._enter_paused,
        }
        self._exit_handlers = {
            State.PRESTART: self._exit_prestart,
            State.GROUSERTEST: self._exit_grouser,
            State.RUBBERTEST: self._exit_rubber,
            State.LOADTEST: self._exit_load,
            State.PAUSED: self._exit_paused,
        }
        self._update_handlers = {
            State.GROUSERTEST: self._update_grouser,
            State.RUBBERTEST: self._update_rubber,
            State.LOADTEST: self._update_load,
        }

    # Public API
    def start_sequence(self, include_grouser: bool):
        seq = []
        if include_grouser:
            seq.append(State.GROUSERTEST)
        seq.extend([State.RUBBERTEST, State.LOADTEST])
        self._sequence = seq
        self._start_next_test()

    def start_test(self):
        if self.state in self._update_handlers:
            self.timer.start()
            self.log_message.emit(f"Started {self.state.name}")

    def stop_test(self):
        if self.timer.isActive():
            self.timer.stop()
            self.log_message.emit(f"Stopped {self.state.name}")
        self._start_next_test()

    def reset(self):
        """
        Abort sequence and return to PRESTART.
        """
        # Stop any running timer
        if self.timer.isActive():
            self.timer.stop()
        # Close logger if open
        if self.logger:
            self.logger.close()
            self.logger = None
        # Clear pending tests and reset time
        self._sequence.clear()
        self._last_test = None
        self.t = 0.0
        # Transition back to PRESTART
        self._change_state(State.PRESTART)
        # Explicitly run the PRESTART entry handler
        self._enter_state(State.PRESTART)

    # Internal transitions
    def _start_next_test(self):
        if self._sequence:
            next_state = self._sequence.pop(0)
            self._enter_test(next_state)
        else:
            self._exit_state(self.state)
            self.reset()

    def _enter_test(self, test_state: State):
        self._exit_state(self.state)
        self.t = 0.0
        self._last_test = test_state
        self._change_state(test_state)
        self._enter_state(test_state)

    def _exit_state(self, state: State):
        handler = self._exit_handlers.get(state)
        if handler:
            handler()

    def _enter_state(self, state: State):
        handler = self._enter_handlers.get(state)
        if handler:
            handler()

    def _change_state(self, new_state: State):
        self.state = new_state
        self.state_changed.emit(self.state)

    def _on_timeout(self):
        handler = self._update_handlers.get(self.state)
        if handler:
            handler()
        self.t += self.interval / 1000.0

    # State-specific methods
    def _enter_prestart(self):
        self.log_message.emit("Entering PRESTART: configure winch")

    def _exit_prestart(self):
        self.log_message.emit("Exiting PRESTART")

    def _enter_grouser(self):
        self.log_message.emit("Entering GROUSERTEST")
        # Close previous logger if any
        if self.logger:
            self.logger.close()
        # Create new logger for this test and report filename
        self.logger = DataLogger(state=self.state)
        self.log_message.emit(f"Logging to {self.logger.filepath}")

    def _update_grouser(self):
        v = math.sin(2*math.pi*1*self.t) + random.uniform(-0.1, 0.1)
        self.data_updated.emit([self.t, v, None, None])
        self.logger.log(self.state, self.t, v, None, None)

    def _exit_grouser(self):
        self.log_message.emit("Exiting GROUSERTEST")
        if self.logger:
            self.logger.close()

    def _enter_rubber(self):
        self.log_message.emit("Entering RUBBERTEST")
        if self.logger:
            self.logger.close()
        self.logger = DataLogger(state=self.state)
        self.log_message.emit(f"Logging to {self.logger.filepath}")

    def _update_rubber(self):
        v = math.sin(2*math.pi*0.5*self.t) + random.uniform(-0.1, 0.1)
        self.data_updated.emit([self.t, None, v, None])
        self.logger.log(self.state, self.t, None, v, None)

    def _exit_rubber(self):
        self.log_message.emit("Exiting RUBBERTEST")
        if self.logger:
            self.logger.close()

    def _enter_load(self):
        self.log_message.emit("Entering LOADTEST")
        if self.logger:
            self.logger.close()
        self.logger = DataLogger(state=self.state)
        self.log_message.emit(f"Logging to {self.logger.filepath}")

    def _update_load(self):
        v = math.sin(2*math.pi*2*self.t) + random.uniform(-0.1, 0.1)
        self.data_updated.emit([self.t, None, None, v])
        self.logger.log(self.state, self.t, None, None, v)

    def _exit_load(self):
        self.log_message.emit("Exiting LOADTEST")
        if self.logger:
            self.logger.close()

    def _enter_paused(self):
        self.log_message.emit("Entering PAUSED")

    def _exit_paused(self):
        self.log_message.emit("Exiting PAUSED")