import unittest
from unittest.mock import patch, MagicMock
from src.scanner.policy_evaluator import PolicyEvaluator

class TestPolicyEvaluator(unittest.TestCase):
    @patch('subprocess.run')
    def test_evaluate_deny(self, mock_run):
        mock_run.return_value = MagicMock(stdout='{"result":[{"expressions":[{"value":true}]}]}', returncode=0)
        evaluator = PolicyEvaluator('policy.rego')
        result = evaluator.evaluate([{'Severity': 'CRITICAL'}])
        self.assertTrue(result['deny'])

    @patch('subprocess.run')
    def test_evaluate_approve(self, mock_run):
        mock_run.return_value = MagicMock(stdout='{"result":[{"expressions":[{"value":false}]}]}', returncode=0)
        evaluator = PolicyEvaluator('policy.rego')
        result = evaluator.evaluate([{'Severity': 'LOW'}])
        self.assertFalse(result['deny'])

if __name__ == '__main__':
    unittest.main()