"""
Policy Evaluator

Evaluates OPA policies against vulnerability scan results.
"""

import subprocess
import json
import logging
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class PolicyEvaluator:
    def __init__(self, policy_path):
        self.policy_path = policy_path

    def evaluate(self, vulnerabilities):
        """
        Evaluate the OPA policy against the vulnerabilities.

        Args:
            vulnerabilities (list): List of processed vulnerabilities.

        Returns:
            dict: Policy decision with 'deny' boolean and messages.
        """
        logger.info("Evaluating policy with OPA")
        input_data = {'vulnerabilities': vulnerabilities}
        input_json = json.dumps(input_data)

        cmd = [
            'opa',
            'eval',
            '--input', '-',
            '--data', self.policy_path,
            '--format', 'json',
            'data.autoaudit.security.deny'
        ]

        try:
            proc = subprocess.run(cmd, input=input_json, capture_output=True, text=True, check=True)
            result = json.loads(proc.stdout)
            deny = False
            messages = []

            # Parse OPA evaluation result
            for expr in result.get('result', []):
                for val in expr.get('expressions', []):
                    if val.get('value') is True:
                        deny = True
                        messages.append("Policy violation detected")

            return {'deny': deny, 'messages': messages}
        except subprocess.CalledProcessError as e:
            logger.error(f"OPA evaluation failed: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OPA output: {e}")
            raise