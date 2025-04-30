from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QComboBox, QInputDialog
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from core.controller import State, Controller

class MainWindow(QMainWindow):
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Manual Sequential Test GUI")

        # State display
        self.state_label = QLabel(f"State: {self.controller.state.name}")

        # Winch controls (PRESTART only)
        self.winch_combo = QComboBox()
        self.winch_combo.addItems(["Grouser", "Rubber", "Load"])
        self.up_btn = QPushButton("UP")
        self.down_btn = QPushButton("DOWN")

        # Single toggle button replaces Start/Stop
        self.toggle_btn = QPushButton("Start Test")
        self.toggle_btn.clicked.connect(self._on_toggle)

        # Sequence and reset
        self.seq_btn = QPushButton("Start Sequence")
        self.reset_btn = QPushButton("Reset")
        self.seq_btn.clicked.connect(self._on_sequence_start)
        self.reset_btn.clicked.connect(self._on_reset)

        # Command window
        self.command_window = QPlainTextEdit()
        self.command_window.setReadOnly(True)
        self.command_window.setPlaceholderText("Command Window")

        # Plot canvases
        titles = ["Grouser", "Rubber", "Load"]
        self.canvases = []
        for title in titles:
            fig = Figure()
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            ax.set_title(title)
            line, = ax.plot([], [])
            canvas.ax = ax
            canvas.line = line
            canvas.xdata = []
            canvas.ydata = []
            self.canvases.append(canvas)

        # Layout assembly
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.state_label)
        top_layout.addWidget(self.winch_combo)
        top_layout.addWidget(self.up_btn)
        top_layout.addWidget(self.down_btn)
        top_layout.addWidget(self.seq_btn)
        top_layout.addWidget(self.toggle_btn)
        top_layout.addWidget(self.reset_btn)

        graphs_layout = QHBoxLayout()
        for c in self.canvases:
            graphs_layout.addWidget(c)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(graphs_layout)
        main_layout.addWidget(self.command_window)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Connect signals
        self.controller.data_updated.connect(self.update_graphs)
        self.controller.state_changed.connect(self._on_state_change)
        self.controller.log_message.connect(self._append_log)

        # Initial UI update
        self._on_state_change(self.controller.state)

        # Emergency stop button, always visible, styled in red
        self.emergency_btn = QPushButton("EMERGENCY STOP")
        self.emergency_btn.setStyleSheet(
        "background-color: red; color: white; font-weight: bold;"
        )
        self.emergency_btn.clicked.connect(self._on_emergency_stop)
        top_layout.addWidget(self.emergency_btn)
    
    def _on_emergency_stop(self):
        # 1) Kill the test timer
        if self.controller.timer.isActive():
            self.controller.timer.stop()
        # 2) Abort sequence and reset state
        self.controller.reset()
        # 3) Close serial if it exists
        if getattr(self, "serial_client", None):
            try:
                self.serial_client.close()
            except Exception as e:
                self.command_window.appendPlainText(
                    f"[Emergency] Error closing serial: {e}"
                )
        # 4) Clear all plots and logs
        self._clear_all()
        self.command_window.appendPlainText("!!! EMERGENCY STOP ACTIVATED !!!")

    def _on_toggle(self):
        # Toggle between start and stop for current test
        if self.controller.timer.isActive():
            # currently running -> stop
            self.controller.stop_test()
            self.toggle_btn.setText("Start Test")
        else:
            # not running -> start
            self.controller.start_test()
            self.toggle_btn.setText("Stop Test")

    def _on_sequence_start(self):
        choice, ok = QInputDialog.getItem(
            self, "Sequence Options", "Include Grouser Test?", ["Yes","No"], 0, False
        )
        if ok:
            include = (choice == "Yes")
            self._clear_all()
            self.controller.start_sequence(include)

    def _on_reset(self):
        self._clear_all()
        self.controller.reset()

    def _on_state_change(self, state: State):
        # Update state label
        self.state_label.setText(f"State: {state.name}")
        # Prestart controls
        pre = (state == State.PRESTART)
        for w in (self.winch_combo, self.up_btn, self.down_btn, self.seq_btn):
            w.setVisible(pre)
        # Toggle only in test states
        running_states = (State.GROUSERTEST, State.RUBBERTEST, State.LOADTEST)
        is_test = (state in running_states)
        self.toggle_btn.setVisible(is_test)
        # Ensure toggle button text matches timer state
        self.toggle_btn.setText(
            "Stop Test" if self.controller.timer.isActive() else "Start Test"
        )
        # Reset always visible
        self.reset_btn.setVisible(True)
        # Command window always visible

    def update_graphs(self, data):
        t, v1, v2, v3 = data
        mapping = {
            State.GROUSERTEST: (0, v1),
            State.RUBBERTEST: (1, v2),
            State.LOADTEST: (2, v3),
        }
        idx, val = mapping.get(self.controller.state, (None, None))
        if idx is not None and val is not None:
            canvas = self.canvases[idx]
            canvas.xdata.append(t)
            canvas.ydata.append(val)
            canvas.line.set_data(canvas.xdata, canvas.ydata)
            canvas.ax.relim()
            canvas.ax.autoscale_view()
            canvas.draw()

    def _append_log(self, msg: str):
        self.command_window.appendPlainText(msg)

    def _clear_all(self):
        # Clear plots and log window
        for c in self.canvases:
            c.xdata.clear(); c.ydata.clear()
            c.line.set_data([], [])
            c.ax.relim(); c.ax.autoscale_view(); c.draw()
        self.command_window.clear()