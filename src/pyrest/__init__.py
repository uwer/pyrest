__version__ = '0.9.0'

import contextlib
import time, os,datetime, sys

@contextlib.contextmanager
def stopwatch(message, context):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        #sys.stderr.write('Total elapsed time for %s at %s : %.3f' % (message,context, t1 - t0))
        print('Total elapsed time for %s at %s : %.3f' % (message,context, t1 - t0), file=sys.stderr, flush=True)