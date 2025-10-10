"""
Container Scanning Orchestrator

This module orchestrates the scanning workflow:
- Invokes Trivy scanner
- Processes vulnerabilities
- Evaluates policies via OPA
- Generates reports
"""

import argparse
import os
import sys
import json
import logging
from src.scanner.trivy_scanner import TrivyScanner
from src.scanner.vulnerability_processor import VulnerabilityProcessor
from src.scanner.policy_evaluator import PolicyEvaluator
from src.scanner.report_generator import ReportGenerator
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Container Security Scanning Orchestrator")
    parser.add_argument('--image', required=True, help='Docker image tag to scan')
    parser.add_argument('--policy', required=True, help='Path to OPA policy file')
    parser.add_argument('--output-dir', default='scan_reports', help='Directory to save scan reports')
    args = parser.parse_args()

    image = args.image
    policy_path = args.policy
    output_dir = args.output_dir

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logger.info(f"Starting scan for image: {image}")

    # Step 1: Run Trivy scan
    trivy = TrivyScanner()
    raw_results = trivy.scan_image(image)

    # Step 2: Process vulnerabilities
    processor = VulnerabilityProcessor()
    processed_results = processor.process(raw_results)

    # Step 3: Evaluate policies
    policy_eval = PolicyEvaluator(policy_path)
    policy_decision = policy_eval.evaluate(processed_results)

    # Step 4: Generate reports
    report_gen = ReportGenerator(output_dir)
    report_paths = report_gen.generate_reports(image, processed_results, policy_decision)

    # Step 5: Output summary and exit code
    critical_vulns = [v for v in processed_results if v['Severity'] == 'CRITICAL']
    high_vulns = [v for v in processed_results if v['Severity'] == 'HIGH']

    logger.info(f"Scan complete. Critical vulnerabilities: {len(critical_vulns)}, High vulnerabilities: {len(high_vulns)}")
    logger.info(f"Policy decision: {'BLOCK' if policy_decision['deny'] else 'APPROVE'}")

    if policy_decision['deny']:
        logger.error("Deployment blocked due to policy violations.")
        sys.exit(1)
    else:
        logger.info("Deployment approved.")
        sys.exit(0)

if __name__ == "__main__":
    main()