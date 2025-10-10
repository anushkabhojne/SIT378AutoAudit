import unittest
import os
import shutil
from src.scanner.report_generator import ReportGenerator

class TestReportGenerator(unittest.TestCase):
    def setUp(self):
        self.output_dir = 'test_reports'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.generator = ReportGenerator(self.output_dir)

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def test_generate_reports(self):
        vulns = [{
            'VulnerabilityID': 'CVE-1234',
            'PkgName': 'openssl',
            'InstalledVersion': '1.1.1',
            'FixedVersion': '1.1.2',
            'Severity': 'HIGH',
            'Description': 'Test vulnerability'
        }]
        policy_decision = {'deny': False, 'messages': []}
        paths = self.generator.generate_reports('test-image:latest', vulns, policy_decision)
        self.assertTrue(os.path.exists(paths['json']))
        self.assertTrue(os.path.exists(paths['sarif']))
        self.assertTrue(os.path.exists(paths['html']))

if __name__ == '__main__':
    unittest.main()