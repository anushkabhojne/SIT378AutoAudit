"""
Metrics Collector Interfaces

Defines abstract base classes for metrics collectors.

Author: Senior Lead, AutoAudit
"""

from abc import ABC, abstractmethod
from typing import Optional

class IMetricsCollector(ABC):
    
    @abstractmethod
    def create_gauge(self, name: str, documentation: str, labelnames=()):
        """
        Create a gauge metric.

        :param name: Metric name.
        :param documentation: Metric description.
        :param labelnames: Optional tuple of label names.
        """
    
        pass

    @abstractmethod
    def create_counter(self, name: str, documentation: str, labelnames=()):
        """
        Create a counter metric.

        :param name: Metric name.
        :param documentation: Metric description.
        :param labelnames: Optional tuple of label names.
        """
        
        pass

    @abstractmethod
    def set_gauge(self, name: str, value: float, labels: Optional[dict] = None):
        """
        Set the value of a gauge metric.

        :param name: Metric name.
        :param value: Value to set.
        :param labels: Optional dictionary of label values.
        """
        
        pass

    @abstractmethod
    def inc_counter(self, name: str, amount: float = 1, labels: Optional[dict] = None):
        """
        Increment a counter metric.

        :param name: Metric name.
        :param amount: Amount to increment.
        :param labels: Optional dictionary of label values.
        """
        
        pass

    @abstractmethod
    def start_http_server(self):
        """
        Start the HTTP server to expose metrics.
        """
        
        pass
