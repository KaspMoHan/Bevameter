import csv
import os
from datetime import datetime

class DataLogger:
    """
    Logs test data to a CSV file. Filename includes timestamp and state.
    """
    def __init__(self, state=None, run_id=None, directory=None):
        # Determine log directory
        if directory is None:
            base = os.path.dirname(__file__)
            directory = os.path.abspath(os.path.join(base, '..', 'logs'))
        os.makedirs(directory, exist_ok=True)
        # Generate a timestamp if not provided
        if run_id is None:
            run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Include state name in filename
        state_name = state.name if state is not None else 'UNKNOWN'
        filename = f'data_{run_id}_{state_name}.csv'
        self.filepath = os.path.join(directory, filename)
        # Open CSV and write header
        self.file = open(self.filepath, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['timestamp', 'state', 't', 'v1', 'v2', 'v3'])

    def log(self, state, t, v1, v2, v3):
        timestamp = datetime.now().isoformat()
        self.writer.writerow([timestamp, state.name, f"{t:.3f}", v1, v2, v3])
        self.file.flush()

    def close(self):
        self.file.close()
