"""
Report Generator

Generates vulnerability scan reports in multiple formats.
"""

import os
import json
import datetime
import logging
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class ReportGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def generate_reports(self, image_tag, vulnerabilities, policy_decision):
        """
        Generate JSON, SARIF, and HTML reports.

        Args:
            image_tag (str): Docker image tag scanned.
            vulnerabilities (list): Processed vulnerabilities.
            policy_decision (dict): Policy evaluation result.

        Returns:
            dict: Paths to generated reports.
        """
        timestamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        base_filename = f"{image_tag.replace(':', '_')}_{timestamp}"

        json_path = os.path.join(self.output_dir, f"{base_filename}.json")
        sarif_path = os.path.join(self.output_dir, f"{base_filename}.sarif")
        html_path = os.path.join(self.output_dir, f"{base_filename}.html")

        logger.info(f"Generating JSON report at {json_path}")
        with open(json_path, 'w') as f:
            json.dump({
                'image': image_tag,
                'vulnerabilities': vulnerabilities,
                'policy_decision': policy_decision,
                'generated_at': timestamp
            }, f, indent=2)

        logger.info(f"Generating SARIF report at {sarif_path}")
        sarif_report = self._generate_sarif(vulnerabilities, image_tag, timestamp)
        with open(sarif_path, 'w') as f:
            json.dump(sarif_report, f, indent=2)

        logger.info(f"Generating HTML report at {html_path}")
        html_report = self._generate_html(vulnerabilities, policy_decision, image_tag, timestamp)
        with open(html_path, 'w') as f:
            f.write(html_report)

        return {
            'json': json_path,
            'sarif': sarif_path,
            'html': html_path
        }

    def _generate_sarif(self, vulnerabilities, image_tag, timestamp):
        """
        Generate SARIF report format.

        Args:
            vulnerabilities (list): Vulnerabilities list.
            image_tag (str): Image tag.
            timestamp (str): Timestamp string.

        Returns:
            dict: SARIF report JSON.
        """
        # Minimal SARIF report structure for vulnerabilities
        runs = [{
            "tool": {
                "driver": {
                    "name": "Trivy",
                    "informationUri": "https://github.com/aquasecurity/trivy",
                    "rules": []
                }
            },
            "results": []
        }]

        rules = {}
        results = []

        for vuln in vulnerabilities:
            rule_id = vuln['VulnerabilityID']
            if rule_id not in rules:
                rules[rule_id] = {
                    "id": rule_id,
                    "shortDescription": {"text": vuln.get('Description', '')[:80]},
                    "helpUri": vuln.get('PrimaryURL', ''),
                    "properties": {
                        "severity": vuln.get('Severity', 'UNKNOWN')
                    }
                }
            results.append({
                "ruleId": rule_id,
                "level": self._sarif_level(vuln.get('Severity', 'UNKNOWN')),
                "message": {
                    "text": f"{vuln.get('PkgName')} {vuln.get('InstalledVersion')} - {vuln.get('Description')}"
                },
                "locations": []
            })

        runs[0]['tool']['driver']['rules'] = list(rules.values())
        runs[0]['results'] = results

        sarif_report = {
            "version": "2.1.0",
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
            "runs": runs
        }
        return sarif_report

    def _sarif_level(self, severity):
        mapping = {
            'CRITICAL': 'error',
            'HIGH': 'error',
            'MEDIUM': 'warning',
            'LOW': 'note',
            'UNKNOWN': 'none'
        }
        return mapping.get(severity.upper(), 'none')

    def _generate_html(self, vulnerabilities, policy_decision, image_tag, timestamp):
        """
        Generate a simple HTML report.

        Args:
            vulnerabilities (list): Vulnerabilities list.
            policy_decision (dict): Policy decision.
            image_tag (str): Image tag.
            timestamp (str): Timestamp string.

        Returns:
            str: HTML content.
        """
        html = f"""
        <html>
        <head><title>Container Scan Report - {image_tag}</title></head>
        <body>
        <h1>Container Security Scan Report</h1>
        <p><strong>Image:</strong> {image_tag}</p>
        <p><strong>Scan Time (UTC):</strong> {timestamp}</p>
        <h2>Policy Decision: {'BLOCK' if policy_decision['deny'] else 'APPROVE'}</h2>
        <h2>Vulnerabilities ({len(vulnerabilities)})</h2>
        <table border="1" cellpadding="5" cellspacing="0">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Package</th>
                    <th>Installed Version</th>
                    <th>Fixed Version</th>
                    <th>Severity</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
        """
        for v in vulnerabilities:
            html += f"""
            <tr>
                <td>{v['VulnerabilityID']}</td>
                <td>{v['PkgName']}</td>
                <td>{v['InstalledVersion']}</td>
                <td>{v.get('FixedVersion', 'N/A')}</td>
                <td>{v['Severity']}</td>
                <td>{v['Description'][:100]}...</td>
            </tr>
            """
        html += """
            </tbody>
        </table>
        </body>
        </html>
        """
        return html