from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from enum import Enum, auto
import math, time, random
import config
from core.data_logger import DataLogger
from core.pid import PID

class State(Enum):
    PRESTART     = auto()
    GROUSERTEST  = auto()
    RUBBERTEST   = auto()
    LOADTEST     = auto()
    PAUSED       = auto()

class Controller(QObject):
    data_updated   = pyqtSignal(list)    # [t, set_len, act_len, output]
    state_changed  = pyqtSignal(State)
    log_message    = pyqtSignal(str)      # GUI log messages

    def __init__(self, interval: int = 100):
        super().__init__()
        # Base interval for state-machine tests
        self.interval      = interval
        self.timer         = QTimer(self)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self._on_timeout)

        # State-machine setup
        self.state         = State.PRESTART
        self._sequence     = []
        self._last_test    = None
        self.t             = 0.0
        self.logger        = None

        self._enter_handlers = {
            State.PRESTART:    self._enter_prestart,
            State.GROUSERTEST: self._enter_grouser,
            State.RUBBERTEST:  self._enter_rubber,
            State.LOADTEST:    self._enter_load,
            State.PAUSED:      self._enter_paused,
        }
        self._exit_handlers = {
            State.PRESTART:    self._exit_prestart,
            State.GROUSERTEST: self._exit_grouser,
            State.RUBBERTEST:  self._exit_rubber,
            State.LOADTEST:    self._exit_load,
            State.PAUSED:      self._exit_paused,
        }
        self._update_handlers = {
            State.GROUSERTEST: self._update_grouser,
            State.RUBBERTEST:  self._update_rubber,
            State.LOADTEST:    self._update_load,
        }

        # Rotation control parameters from config
        self.rotation_deg   = config.ROTATION_DEG
        self.rotation_time  = config.ROTATION_TIME
        self.frequency      = config.CONTROL_FREQUENCY  # Hz

        # Derived rotation timing
        self.dt_s           = 1.0 / self.frequency
        self.dt_ms          = int(self.dt_s * 1000)
        self.omega          = math.radians(self.rotation_deg) / self.rotation_time

        # Precompute rotation trajectory (length setpoints)
        steps = int(self.rotation_time * self.frequency) + 1
        self._times       = [i * self.dt_s for i in range(steps)]
        self._setpoints   = [
            math.hypot(
                955.9 + 247.5 * math.sin(self.omega * t),
                247.5 * math.cos(self.omega * t)
            ) for t in self._times
        ]

        # PID for length control
        self.pid = PID(
            kp=config.PID_KP,
            ki=config.PID_KI,
            kd=config.PID_KD,
            setpoint=0.0,
            sample_time=self.dt_s,
            output_limits=(config.MIN_SPEED, config.MAX_SPEED)
        )

        # Rotation state flags
        self._rotation_active = False
        self._rotation_index  = 0

    # --- Rotation control API ---------------------------------------------
    def start_rotation(self):
        """
        Begin closed-loop rotation: rotate rotation_deg over rotation_time seconds.
        """
        self.pid.reset()
        self._rotation_active = True
        self._rotation_index  = 0
        self.t = 0.0
        # Use rotation timer interval
        self.timer.setInterval(self.dt_ms)
        self.timer.start()
        self.log_message.emit("Rotation started")

    def stop_rotation(self):
        """
        Stop rotation and revert to state-machine timing.
        """
        self._rotation_active = False
        self.timer.stop()
        self.timer.setInterval(self.interval)
        self.log_message.emit("Rotation stopped")

    # --- Internal timer callback ------------------------------------------
    def _on_timeout(self):
        if self._rotation_active:
            self._update_rotation()
        else:
            handler = self._update_handlers.get(self.state)
            if handler:
                handler()
        # Advance elapsed time
        delta = self.dt_s if self._rotation_active else (self.interval / 1000.0)
        self.t += delta

    def _update_rotation(self):
        # Check completion
        if self._rotation_index >= len(self._setpoints):
            self.stop_rotation()
            return

        # Current time and setpoint
        t        = self._times[self._rotation_index]
        l_set    = self._setpoints[self._rotation_index]
        # TODO: implement actual measurement reading
        l_act    = 0.0

        # PID-only control
        self.pid.setpoint = l_set
        corr = self.pid.update(l_act, current_time=time.time())
        if corr is None:
            return
        output = corr

        # Emit data for plotting/log
        self.data_updated.emit([t, l_set, l_act, output])
        self.log_message.emit(
            f"t={t:.2f}s set={l_set:.2f} act={l_act:.2f} -> {output:.2f}"
        )

        self._rotation_index += 1

    # --- Existing state-machine methods ----------------------------------
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
        if self.timer.isActive():
            self.timer.stop()
        if self.logger:
            self.logger.close()
            self.logger = None
        self._sequence.clear()
        self._last_test = None
        self.t = 0.0
        self._rotation_active = False
        self._rotation_index = 0
        self._change_state(State.PRESTART)
        self._enter_state(State.PRESTART)

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

    # State-specific handlers unchanged...
    def _enter_prestart(self):
        self.log_message.emit("Entering PRESTART: configure winch")

    def _exit_prestart(self):
        self.log_message.emit("Exiting PRESTART")

    def _enter_grouser(self):
        self.log_message.emit("Entering GROUSERTEST")
        if self.logger:
            self.logger.close()
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
