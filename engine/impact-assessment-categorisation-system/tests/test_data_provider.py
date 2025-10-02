import unittest
from data_provider.data_provider import DataProvider

class TestDataProvider(unittest.TestCase):
    def setUp(self):
        self.dp = DataProvider()

    def test_get_data(self):
        data = self.dp.get_data('test_source')
        self.assertIsInstance(data, dict)

if __name__ == '__main__':
    unittest.main()
