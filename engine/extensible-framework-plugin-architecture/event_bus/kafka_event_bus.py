"""
Kafka Event Bus Implementation

Provides a Kafka-based event bus for publishing and subscribing to events.

Author: Senior Lead, AutoAudit
"""

import asyncio
import logging
from typing import Callable, Any, Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from .interfaces import IEventBus

class KafkaEventBus(IEventBus):
    
    def __init__(self, bootstrap_servers: str, topic: str, group_id: Optional[str] = None):
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id or "default-group"
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._logger = logging.getLogger(self.__class__.__name__)
        self._running = False

    async def start(self):
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
        await self._producer.start()
        self._logger.info("Kafka producer started")

        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            auto_offset_reset="earliest"
        )
        
        await self._consumer.start()
        self._logger.info("Kafka consumer started")
        self._running = True

    async def stop(self):
        
        if self._producer:
            await self._producer.stop()
            self._logger.info("Kafka producer stopped")
        
        if self._consumer:
            await self._consumer.stop()
            self._logger.info("Kafka consumer stopped")
        
        self._running = False

    async def publish(self, event: bytes):
        
        if not self._producer:
            raise RuntimeError("Producer not started")
        
        await self._producer.send_and_wait(self._topic, event)
        self._logger.debug(f"Published event to topic {self._topic}")

    async def subscribe(self, handler: Callable[[bytes], Any]):
        
        if not self._consumer:
            raise RuntimeError("Consumer not started")
        
        self._logger.info(f"Starting subscription to topic {self._topic}")
        
        try:
            
            async for msg in self._consumer:
                self._logger.debug(f"Received message: {msg.value}")
                await handler(msg.value)
                
                if not self._running:
                    break
        
        except asyncio.CancelledError:
            self._logger.info("Subscription cancelled")
        
        except Exception as e:
            self._logger.error(f"Error in subscription: {e}")
