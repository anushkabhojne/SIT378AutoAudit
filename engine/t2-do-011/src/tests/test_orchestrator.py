import unittest
from unittest.mock import patch, MagicMock
import src.scanner.orchestrator as orchestrator

class TestOrchestrator(unittest.TestCase):
    @patch('src.scanner.orchestrator.TrivyScanner')
    @patch('src.scanner.orchestrator.VulnerabilityProcessor')
    @patch('src.scanner.orchestrator.PolicyEvaluator')
    @patch('src.scanner.orchestrator.ReportGenerator')
    def test_main_approve(self, mock_report, mock_policy, mock_processor, mock_trivy):
        mock_trivy.return_value.scan_image.return_value = [{'Severity': 'LOW'}]
        mock_processor.return_value.process.return_value = [{'Severity': 'LOW'}]
        mock_policy.return_value.evaluate.return_value = {'deny': False, 'messages': []}
        mock_report.return_value.generate_reports.return_value = {'json': 'path'}

        with patch('sys.exit') as mock_exit:
            orchestrator.main()
            mock_exit.assert_called_with(0)

    @patch('src.scanner.orchestrator.TrivyScanner')
    @patch('src.scanner.orchestrator.VulnerabilityProcessor')
    @patch('src.scanner.orchestrator.PolicyEvaluator')
    @patch('src.scanner.orchestrator.ReportGenerator')
    def test_main_deny(self, mock_report, mock_policy, mock_processor, mock_trivy):
        mock_trivy.return_value.scan_image.return_value = [{'Severity': 'CRITICAL'}]
        mock_processor.return_value.process.return_value = [{'Severity': 'CRITICAL'}]
        mock_policy.return_value.evaluate.return_value = {'deny': True, 'messages': ['Critical vuln']}

        with patch('sys.exit') as mock_exit:
            orchestrator.main()
            mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()