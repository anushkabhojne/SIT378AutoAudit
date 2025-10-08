"""
Prometheus Metrics Collector

Collects and exposes metrics in Prometheus format.

Author: Senior Lead, AutoAudit
"""

from prometheus_client import CollectorRegistry, Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.exposition import start_http_server
import asyncio
import logging
from typing import Optional

class PrometheusCollector:
    
    def __init__(self, port: int = 8000):
        self._registry = CollectorRegistry()
        self._port = port
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gauges = {}
        self._counters = {}

    def create_gauge(self, name: str, documentation: str, labelnames = ()):
        gauge = Gauge(name, documentation, labelnames = labelnames, registry = self._registry)
        self._gauges[name] = gauge
        self._logger.debug(f"Created gauge metric: {name}")
        return gauge

    def create_counter(self, name: str, documentation: str, labelnames = ()):
        counter = Counter(name, documentation, labelnames = labelnames, registry = self._registry)
        self._counters[name] = counter
        self._logger.debug(f"Created counter metric: {name}")
        return counter

    def set_gauge(self, name: str, value: float, labels: Optional[dict] = None):
        gauge = self._gauges.get(name)
        
        if not gauge:
            self._logger.error(f"Gauge {name} not found")
            return
        
        if labels:
            gauge.labels(**labels).set(value)
        
        else:
            gauge.set(value)
        
        self._logger.debug(f"Set gauge {name} to {value} with labels {labels}")

    def inc_counter(self, name: str, amount: float = 1, labels: Optional[dict] = None):
        counter = self._counters.get(name)
        
        if not counter:
            self._logger.error(f"Counter {name} not found")
            return
        
        if labels:
            counter.labels(**labels).inc(amount)
        
        else:
            counter.inc(amount)
        
        self._logger.debug(f"Incremented counter {name} by {amount} with labels {labels}")

    def start_http_server(self):
        start_http_server(self._port, registry=self._registry)
        self._logger.info(f"Prometheus metrics HTTP server started on port {self._port}")
