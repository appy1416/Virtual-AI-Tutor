import os
import logging
import threading

logger = logging.getLogger("edutwin.tasks")

CELERY_AVAILABLE = False

class FakeTask:
    def __init__(self, func):
        self.func = func
        
    def delay(self, *args, **kwargs):
        if os.getenv("TESTING") == "True":
            # Skip background execution in test environment to avoid DB session overlaps
            return
        # Run in a background thread to prevent blocking
        thread = threading.Thread(target=self.func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

class FakeCelery:
    def task(self, *args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return FakeTask(args[0])
        def decorator(func):
            return FakeTask(func)
        return decorator

celery_app = FakeCelery()

