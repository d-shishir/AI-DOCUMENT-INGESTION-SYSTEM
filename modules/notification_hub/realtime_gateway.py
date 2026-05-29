import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)

# List of active asyncio queues for SSE listeners
_active_listeners: List[asyncio.Queue] = []

def register_listener(queue: asyncio.Queue):
    """
    Registers a new asyncio Queue representing an SSE client connection.
    """
    _active_listeners.append(queue)
    logger.info(f"Realtime Gateway: Registered new client connection (Active: {len(_active_listeners)})")

def unregister_listener(queue: asyncio.Queue):
    """
    Unregisters an SSE client connection queue.
    """
    if queue in _active_listeners:
        _active_listeners.remove(queue)
        logger.info(f"Realtime Gateway: Unregistered client connection (Active: {len(_active_listeners)})")

def broadcast_notification(notification_dict: dict):
    """
    Broadcasts a notification dictionary to all active SSE queues.
    """
    if not _active_listeners:
        return
        
    logger.info(f"Realtime Gateway: Broadcasting to {len(_active_listeners)} active clients")
    
    # Try pushing to all loops
    for queue in _active_listeners:
        try:
            queue.put_nowait(notification_dict)
        except Exception as e:
            logger.warning(f"Realtime Gateway: Failed to push to client queue: {str(e)}")
