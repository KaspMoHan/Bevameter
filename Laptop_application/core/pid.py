import time

class PID:
    """
    A simple PID controller.

    Attributes:
        kp (float): Proportional gain
        ki (float): Integral gain
        kd (float): Derivative gain
        setpoint (float): Desired target value
        sample_time (float): Minimum time (seconds) between updates
        output_limits (tuple): (min, max) limits for the controller output
    """
    def __init__(self, kp: float, ki: float, kd: float,
                 setpoint: float = 0.0,
                 sample_time: float = 0.1,
                 output_limits: tuple = (None, None)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.sample_time = sample_time
        self.min_output, self.max_output = output_limits

        self._last_time = None
        self._last_error = 0.0
        self._integral = 0.0

    def reset(self):
        """
        Resets the PID internals (integral term and last error/time).
        """
        self._last_time = None
        self._last_error = 0.0
        self._integral = 0.0

    def update(self, measurement: float, current_time: float = None) -> float:
        """
        Calculate PID output value for given measurement.

        Args:
            measurement (float): The current measured value.
            current_time (float): The current time in seconds (defaults to time.time()).

        Returns:
            float: Control output.
        """
        if current_time is None:
            current_time = time.time()

        # Initialize last_time on first call
        if self._last_time is None:
            self._last_time = current_time
            self._last_error = self.setpoint - measurement

        # Compute time difference
        dt = current_time - self._last_time
        if dt < self.sample_time:
            # Not enough time has passed
            return None

        # Error term
        error = self.setpoint - measurement

        # Proportional term
        p = self.kp * error

        # Integral term with anti-windup via clamping
        self._integral += error * dt
        i = self.ki * self._integral

        # Derivative term
        derivative = (error - self._last_error) / dt
        d = self.kd * derivative

        # Compute raw output
        output = p + i + d

        # Clamp output to limits
        if (self.min_output is not None) and (output < self.min_output):
            output = self.min_output
        if (self.max_output is not None) and (output > self.max_output):
            output = self.max_output

        # Save state for next iteration
        self._last_time = current_time
        self._last_error = error

        return output