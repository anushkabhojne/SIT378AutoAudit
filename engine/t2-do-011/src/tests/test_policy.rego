package autoaudit.security

test_deny_critical {
    deny[msg]
    some i
    input := {"vulnerabilities": [{"Severity": "CRITICAL", "VulnerabilityID": "CVE-0001"}]}
    msg == sprintf("Critical vulnerability detected: %v", [input.vulnerabilities[i].VulnerabilityID])
}

test_warn_high {
    warn[msg]
    some i
    input := {"vulnerabilities": [{"Severity": "HIGH", "VulnerabilityID": "CVE-0002"}]}
    msg == sprintf("High severity vulnerability detected: %v", [input.vulnerabilities[i].VulnerabilityID])
}