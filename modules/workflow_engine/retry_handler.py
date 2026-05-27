import time
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class RetryHandler:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 0.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def execute_with_retry(
        self,
        step_name: str,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> tuple[Any, int, str | None]:
        """
        Executes a step function with retries and exponential backoff.
        Returns: (result, attempts, error_message)
        """
        attempts = 0
        last_error = None
        
        while attempts <= self.max_retries:
            try:
                if attempts > 0:
                    wait_time = self.backoff_factor * (2 ** (attempts - 1))
                    logger.info(f"Retrying step '{step_name}' (Attempt {attempts}/{self.max_retries}) after {wait_time}s...")
                    time.sleep(wait_time)
                
                result = func(*args, **kwargs)
                return result, attempts, None
            except Exception as e:
                attempts += 1
                last_error = str(e)
                logger.error(f"Error executing step '{step_name}' on attempt {attempts}: {last_error}")
        
        return None, attempts - 1, last_error
