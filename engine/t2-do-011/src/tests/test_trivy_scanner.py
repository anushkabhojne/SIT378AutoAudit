import unittest
from unittest.mock import patch, MagicMock
from src.scanner.trivy_scanner import TrivyScanner

class TestTrivyScanner(unittest.TestCase):
    @patch('subprocess.run')
    def test_scan_image_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout='{"Results":[{"Vulnerabilities":[{"VulnerabilityID":"CVE-1234","PkgName":"openssl","InstalledVersion":"1.1.1","Severity":"HIGH"}]}]}', returncode=0)
        scanner = TrivyScanner()
        vulns = scanner.scan_image('test-image:latest')
        self.assertEqual(len(vulns), 1)
        self.assertEqual(vulns[0]['VulnerabilityID'], 'CVE-1234')

    @patch('subprocess.run')
    def test_scan_image_failure(self, mock_run):
        mock_run.side_effect = Exception("Scan failed")
        scanner = TrivyScanner()
        with self.assertRaises(Exception):
            scanner.scan_image('test-image:latest')

if __name__ == '__main__':
    unittest.main()