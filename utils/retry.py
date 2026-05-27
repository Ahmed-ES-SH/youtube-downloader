import time
import functools


def with_retry(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            wait = delay
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    print(f"  \u26a0 Attempt {attempt} failed: {e}. Retrying in {wait:.0f}s...")
                    time.sleep(wait)
                    wait *= backoff
        return wrapper
    return decorator
