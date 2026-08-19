"""A terminal loading spinner for long-running operations."""

import sys
import time
import threading
from contextlib import contextmanager


@contextmanager
def loading_animation(message: str):
    """
    A context manager that displays a CLI loading animation
    while a block of code is executing.
    """
    stop_event = threading.Event()

    def animate():
        # Sleek Braille spinner characters
        chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        while not stop_event.is_set():
            # \r returns the cursor to the beginning of the line
            sys.stdout.write(f"\r{message} {chars[i % len(chars)]}")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1

        # Clear the loading line once finished
        sys.stdout.write(f"\r{' ' * (len(message) + 4)}\r")
        sys.stdout.flush()

    # Start the animation in a separate thread
    t = threading.Thread(target=animate)
    t.start()

    try:
        yield
    finally:
        # Signal the thread to stop and wait for it to finish
        stop_event.set()
        t.join()
