"""
Event Bus Interfaces

Defines abstract base classes for event bus implementations.

Author: Senior Lead, AutoAudit
"""

from abc import ABC, abstractmethod
from typing import Callable, Any

class IEventBus(ABC):
    @abstractmethod
    async def start(self):
        """
        Start the event bus to initialise connections.
        """
    
        pass

    @abstractmethod
    async def stop(self):
        """
        Stop the event bus and close connections.
        """
    
        pass

    @abstractmethod
    async def publish(self, event: bytes):
        """
        Publish an event to the bus.

        :param event: Event data as bytes.
        """
    
        pass

    @abstractmethod
    async def subscribe(self, handler: Callable[[bytes], Any]):
        """
        Subscribe to events from the bus.

        :param handler: Async callable to handle incoming event bytes.
        """
    
        pass
