
class timeit():
    """calculate some timing information"""

    def __init__(self):
        self.start = None

    def __call__(self):
        if self.start is None:
            self.start = time.time()
            return 0
        else:
            stop = time.time()
            dt = stop-self.start
            self.start = stop
            return dt


