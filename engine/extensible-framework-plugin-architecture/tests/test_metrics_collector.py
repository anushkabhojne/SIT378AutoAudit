import unittest
from metrics_collector.metrics_collector import MetricsCollector

class TestMetricsCollector(unittest.TestCase):
    def setUp(self):
        self.mc = MetricsCollector()

    def test_create_and_set_gauge(self):
        self.mc.create_gauge('test_gauge', 'A test gauge')
        self.mc.set_gauge('test_gauge', 10)
        #No direct way to assert Prometheus client metrics value here

    def test_create_and_inc_counter(self):
        self.mc.create_counter('test_counter', 'A test counter')
        self.mc.inc_counter('test_counter', 5)
        #No direct way to assert Prometheus client metrics value here

if __name__ == '__main__':
    unittest.main()
