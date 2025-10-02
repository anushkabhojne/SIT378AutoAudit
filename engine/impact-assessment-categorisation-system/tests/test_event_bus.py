import unittest
from event_bus.event_bus import EventBus

class TestEventBus(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()

    def test_subscribe_and_publish(self):
        results = []

        def handler(event):
            results.append(event)

        self.bus.subscribe('test_event', handler)
        self.bus.publish('test_event', {'key': 'value'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], {'key': 'value'})

if __name__ == '__main__':
    unittest.main()
