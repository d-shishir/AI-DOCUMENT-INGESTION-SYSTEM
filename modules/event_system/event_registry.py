import logging
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)

class EventRegistry:
    def __init__(self):
        # Maps event_type -> list of subscriber callback functions
        self._subscriptions: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """
        Registers a callback function to trigger whenever a specific event_type is published.
        The callback function signature should be: callback(event_record, db_session)
        """
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        self._subscriptions[event_type].append(callback)
        logger.info(f"Registered subscriber callback for event type '{event_type}': {callback.__name__ if hasattr(callback, '__name__') else str(callback)}")

    def get_subscribers(self, event_type: str) -> List[Callable]:
        return self._subscriptions.get(event_type, [])

event_registry = EventRegistry()
