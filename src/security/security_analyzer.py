"""Enterprise-Grade Security Analysis and Compliance Scanner."""

import re
import ast
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..common.logging import get_logger
from ..plan_management.models import Plan

logger = get_logger("security_analyzer")


class VulnerabilityLevel(str, Enum):
    """Security vulnerability severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceStandard(str, Enum):
    """Supported compliance standards."""

    GDPR = "gdpr"
    CCPA = "ccpa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    SOX = "sox"
    NIST = "nist"
    ISO_27001 = "iso_27001"


@dataclass
class SecurityVulnerability:
    """Represents a security vulnerability found in code."""

    id: str
    title: str
    description: str
    severity: VulnerabilityLevel
    line_number: int
    code_snippet: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    remediation: str = ""
    confidence: float = 0.0


@dataclass
class ComplianceCheck:
    """Represents a compliance check result."""

    standard: ComplianceStandard
    requirement_id: str
    requirement_name: str
    status: str  # "pass", "fail", "warning", "not_applicable"
    details: str
    evidence: List[str] = field(default_factory=list)
    remediation_steps: List[str] = field(default_factory=list)


@dataclass
class SecurityReport:
    """Comprehensive security analysis report."""

    scan_id: str
    timestamp: datetime
    code_hash: str
    vulnerabilities: List[SecurityVulnerability]
    compliance_status: List[ComplianceCheck]
    security_score: float
    recommendations: List[str]
    risk_assessment: Dict[str, Any]
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)


class SecurityPatternDetector:
    """Detects security anti-patterns and vulnerabilities in code."""

    def __init__(self):
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.crypto_patterns = self._load_crypto_patterns()
        self.injection_patterns = self._load_injection_patterns()

    def _load_vulnerability_patterns(self) -> Dict[str, Dict]:
        """Load vulnerability detection patterns."""
        return {
            # SQL Injection patterns
            "sql_injection": {
                "patterns": [
                    r"execute\s*\(\s*[\"'][^\"']*\+[^\"']*[\"']\s*\)",
                    r"cursor\.execute\s*\(\s*[\"'][^\"']*%[^\"']*[\"']\s*%",
                    r"query\s*=\s*[\"'][^\"']*\+[^\"']*[\"']",
                    r"SELECT\s+.*\+.*FROM",
                    r"INSERT\s+.*\+.*VALUES",
                ],
                "severity": VulnerabilityLevel.HIGH,
                "cwe_id": "CWE-89",
                "owasp": "A03:2021-Injection",
            },
            # Cross-Site Scripting (XSS)
            "xss": {
                "patterns": [
                    r"innerHTML\s*=\s*.*\+",
                    r"document\.write\s*\(\s*.*\+",
                    r"\.html\s*\(\s*.*\+",
                    r"render_template_string\s*\(",
                    r"Markup\s*\(\s*.*\+.*\)",
                ],
                "severity": VulnerabilityLevel.HIGH,
                "cwe_id": "CWE-79",
                "owasp": "A03:2021-Injection",
            },
            # Hardcoded credentials
            "hardcoded_credentials": {
                "patterns": [
                    r"password\s*=\s*[\"'][^\"']{3,}[\"']",
                    r"api_key\s*=\s*[\"'][^\"']{10,}[\"']",
                    r"secret\s*=\s*[\"'][^\"']{8,}[\"']",
                    r"token\s*=\s*[\"'][^\"']{10,}[\"']",
                    r"AWS_SECRET_ACCESS_KEY\s*=\s*[\"'][^\"']+[\"']",
                    r"private_key\s*=\s*[\"'][^\"']+[\"']",
                ],
                "severity": VulnerabilityLevel.CRITICAL,
                "cwe_id": "CWE-798",
                "owasp": "A07:2021-Identification and Authentication Failures",
            },
            # Insecure random generation
            "weak_random": {
                "patterns": [
                    r"random\.random\(\)",
                    r"Math\.random\(\)",
                    r"rand\(\)",
                    r"random\.randint\(",
                    r"random\.choice\(",
                ],
                "severity": VulnerabilityLevel.MEDIUM,
                "cwe_id": "CWE-338",
                "owasp": "A02:2021-Cryptographic Failures",
            },
            # Path traversal
            "path_traversal": {
                "patterns": [
                    r"open\s*\(\s*.*\+.*[\"']\.\./",
                    r"os\.path\.join\s*\(\s*.*user",
                    r"pathlib\.Path\s*\(\s*.*input",
                    r"file_path\s*=\s*.*request",
                ],
                "severity": VulnerabilityLevel.HIGH,
                "cwe_id": "CWE-22",
                "owasp": "A01:2021-Broken Access Control",
            },
            # Command injection
            "command_injection": {
                "patterns": [
                    r"os\.system\s*\(\s*.*\+",
                    r"subprocess\.call\s*\(\s*.*\+",
                    r"subprocess\.run\s*\(\s*.*\+",
                    r"os\.popen\s*\(\s*.*\+",
                    r"exec\s*\(\s*.*input",
                ],
                "severity": VulnerabilityLevel.CRITICAL,
                "cwe_id": "CWE-78",
                "owasp": "A03:2021-Injection",
            },
        }

    def _load_crypto_patterns(self) -> Dict[str, Dict]:
        """Load cryptographic vulnerability patterns."""
        return {
            "weak_encryption": {
                "patterns": [
                    r"DES\(",
                    r"3DES\(",
                    r"MD5\(",
                    r"SHA1\(",
                    r"RC4\(",
                    r"ECB\s*mode",
                ],
                "severity": VulnerabilityLevel.HIGH,
                "cwe_id": "CWE-327",
            },
            "hardcoded_crypto_key": {
                "patterns": [
                    r"AES\.new\s*\(\s*[\"'][^\"']{16,}[\"']",
                    r"key\s*=\s*[\"'][0-9a-fA-F]{32,}[\"']",
                    r"iv\s*=\s*[\"'][0-9a-fA-F]{16,}[\"']",
                ],
                "severity": VulnerabilityLevel.CRITICAL,
                "cwe_id": "CWE-798",
            },
        }

    def _load_injection_patterns(self) -> Dict[str, Dict]:
        """Load injection vulnerability patterns."""
        return {
            "ldap_injection": {
                "patterns": [r"ldap.*search.*\+", r"ldap.*filter.*%"],
                "severity": VulnerabilityLevel.HIGH,
                "cwe_id": "CWE-90",
            },
            "xpath_injection": {
                "patterns": [r"xpath.*\+", r"evaluate.*\+"],
                "severity": VulnerabilityLevel.HIGH,
                "cwe_id": "CWE-91",
            },
        }

    def scan_code(
        self, code: str, filename: str = "unknown"
    ) -> List[SecurityVulnerability]:
        """Scan code for security vulnerabilities."""
        vulnerabilities = []
        lines = code.split("\n")

        # Combine all pattern dictionaries
        all_patterns = {
            **self.vulnerability_patterns,
            **self.crypto_patterns,
            **self.injection_patterns,
        }

        for vuln_type, config in all_patterns.items():
            for pattern in config["patterns"]:
                vulnerabilities.extend(
                    self._find_pattern_matches(
                        lines, pattern, vuln_type, config, filename
                    )
                )

        # Additional AST-based analysis for Python code
        if filename.endswith(".py"):
            vulnerabilities.extend(self._ast_security_analysis(code, filename))

        return vulnerabilities

    def _find_pattern_matches(
        self,
        lines: List[str],
        pattern: str,
        vuln_type: str,
        config: Dict,
        filename: str,
    ) -> List[SecurityVulnerability]:
        """Find pattern matches in code lines."""
        vulnerabilities = []
        compiled_pattern = re.compile(pattern, re.IGNORECASE)

        for line_num, line in enumerate(lines, 1):
            matches = compiled_pattern.findall(line)
            if matches:
                vuln_id = f"{vuln_type}_{hashlib.md5(f'{filename}_{line_num}_{line}'.encode()).hexdigest()[:8]}"

                vulnerability = SecurityVulnerability(
                    id=vuln_id,
                    title=self._get_vulnerability_title(vuln_type),
                    description=self._get_vulnerability_description(vuln_type),
                    severity=config["severity"],
                    line_number=line_num,
                    code_snippet=line.strip(),
                    cwe_id=config.get("cwe_id"),
                    owasp_category=config.get("owasp"),
                    remediation=self._get_remediation_advice(vuln_type),
                    confidence=self._calculate_confidence(vuln_type, line),
                )

                vulnerabilities.append(vulnerability)

        return vulnerabilities

    def _ast_security_analysis(
        self, code: str, filename: str
    ) -> List[SecurityVulnerability]:
        """Perform AST-based security analysis for Python code."""
        vulnerabilities = []

        try:
            tree = ast.parse(code)
            visitor = SecurityASTVisitor(filename)
            visitor.visit(tree)
            vulnerabilities.extend(visitor.vulnerabilities)
        except SyntaxError as e:
            logger.warning(f"Could not parse {filename} for AST analysis: {e}")

        return vulnerabilities

    def _get_vulnerability_title(self, vuln_type: str) -> str:
        """Get human-readable title for vulnerability type."""
        titles = {
            "sql_injection": "SQL Injection Vulnerability",
            "xss": "Cross-Site Scripting (XSS) Vulnerability",
            "hardcoded_credentials": "Hardcoded Credentials",
            "weak_random": "Weak Random Number Generation",
            "path_traversal": "Path Traversal Vulnerability",
            "command_injection": "Command Injection Vulnerability",
            "weak_encryption": "Weak Cryptographic Algorithm",
            "hardcoded_crypto_key": "Hardcoded Cryptographic Key",
            "ldap_injection": "LDAP Injection Vulnerability",
            "xpath_injection": "XPath Injection Vulnerability",
        }
        return titles.get(vuln_type, f"Security Issue: {vuln_type}")

    def _get_vulnerability_description(self, vuln_type: str) -> str:
        """Get detailed description for vulnerability type."""
        descriptions = {
            "sql_injection": "Code contains potential SQL injection vulnerability where user input is directly concatenated into SQL queries.",
            "xss": "Code contains potential Cross-Site Scripting vulnerability where user input is rendered without proper sanitization.",
            "hardcoded_credentials": "Sensitive credentials are hardcoded in the source code, which poses a significant security risk.",
            "weak_random": "Code uses weak random number generation which may be predictable for security-sensitive operations.",
            "path_traversal": "Code contains potential path traversal vulnerability allowing unauthorized file system access.",
            "command_injection": "Code contains potential command injection vulnerability where user input is passed to system commands.",
            "weak_encryption": "Code uses weak or deprecated cryptographic algorithms that are vulnerable to attacks.",
            "hardcoded_crypto_key": "Cryptographic keys are hardcoded in the source code, compromising security.",
            "ldap_injection": "Code contains potential LDAP injection vulnerability in directory service queries.",
            "xpath_injection": "Code contains potential XPath injection vulnerability in XML queries.",
        }
        return descriptions.get(
            vuln_type, f"Security vulnerability of type: {vuln_type}"
        )

    def _get_remediation_advice(self, vuln_type: str) -> str:
        """Get remediation advice for vulnerability type."""
        remediations = {
            "sql_injection": "Use parameterized queries or prepared statements instead of string concatenation.",
            "xss": "Sanitize and validate all user input. Use proper encoding for output contexts.",
            "hardcoded_credentials": "Store credentials in environment variables or secure configuration files.",
            "weak_random": "Use cryptographically secure random number generators (e.g., secrets.SystemRandom).",
            "path_traversal": "Validate and sanitize file paths. Use allow-lists for permitted directories.",
            "command_injection": "Avoid executing system commands with user input. Use safe APIs instead.",
            "weak_encryption": "Use strong, modern cryptographic algorithms (AES-256, SHA-256, etc.).",
            "hardcoded_crypto_key": "Generate keys dynamically or store them securely outside the codebase.",
            "ldap_injection": "Use proper LDAP escaping and parameterized queries.",
            "xpath_injection": "Use parameterized XPath queries and input validation.",
        }
        return remediations.get(vuln_type, "Review and apply security best practices.")

    def _calculate_confidence(self, vuln_type: str, code_line: str) -> float:
        """Calculate confidence score for vulnerability detection."""
        base_confidence = 0.7

        # Increase confidence for obvious patterns
        high_confidence_patterns = [
            "password =",
            "api_key =",
            "secret =",
            "execute(",
            "innerHTML =",
        ]
        if any(pattern in code_line.lower() for pattern in high_confidence_patterns):
            base_confidence += 0.2

        # Decrease confidence for comments or string literals
        if code_line.strip().startswith("#") or code_line.strip().startswith("//"):
            base_confidence -= 0.3

        return max(0.1, min(1.0, base_confidence))


class SecurityASTVisitor(ast.NodeVisitor):
    """AST visitor for Python security analysis."""

    def __init__(self, filename: str):
        self.filename = filename
        self.vulnerabilities = []
        self.current_line = 1

    def visit_Call(self, node):
        """Visit function calls for security analysis."""
        # Check for dangerous function calls
        if hasattr(node.func, "id"):
            func_name = node.func.id
            if func_name in ["eval", "exec", "compile"]:
                self._add_vulnerability(
                    "dangerous_function",
                    f"Use of dangerous function: {func_name}",
                    VulnerabilityLevel.HIGH,
                    node.lineno,
                )

        # Check for subprocess calls with shell=True
        if (
            hasattr(node.func, "attr")
            and node.func.attr in ["call", "run", "Popen"]
            and hasattr(node.func, "value")
            and hasattr(node.func.value, "id")
            and node.func.value.id == "subprocess"
        ):

            for keyword in node.keywords:
                if (
                    keyword.arg == "shell"
                    and hasattr(keyword.value, "value")
                    and keyword.value.value is True
                ):
                    self._add_vulnerability(
                        "shell_injection",
                        "subprocess call with shell=True is dangerous",
                        VulnerabilityLevel.HIGH,
                        node.lineno,
                    )

        self.generic_visit(node)

    def visit_Import(self, node):
        """Visit import statements."""
        for alias in node.names:
            if alias.name in ["pickle", "cPickle", "dill"]:
                self._add_vulnerability(
                    "insecure_deserialization",
                    f"Import of {alias.name} module can lead to insecure deserialization",
                    VulnerabilityLevel.MEDIUM,
                    node.lineno,
                )

        self.generic_visit(node)

    def _add_vulnerability(
        self,
        vuln_type: str,
        description: str,
        severity: VulnerabilityLevel,
        line_no: int,
    ):
        """Add a vulnerability to the list."""
        vuln_id = f"{vuln_type}_{hashlib.md5(f'{self.filename}_{line_no}'.encode()).hexdigest()[:8]}"

        vulnerability = SecurityVulnerability(
            id=vuln_id,
            title=f"AST Analysis: {vuln_type}",
            description=description,
            severity=severity,
            line_number=line_no,
            code_snippet="",  # Could be extracted from source
            remediation=f"Review and secure {vuln_type}",
            confidence=0.8,
        )

        self.vulnerabilities.append(vulnerability)


class ComplianceChecker:
    """Checks code and plans for compliance with various standards."""

    def __init__(self):
        self.compliance_rules = self._load_compliance_rules()

    def _load_compliance_rules(self) -> Dict[ComplianceStandard, Dict]:
        """Load compliance rules for different standards."""
        return {
            ComplianceStandard.GDPR: {
                "data_protection": {
                    "description": "Personal data must be processed lawfully and securely",
                    "checks": [
                        "encryption_check",
                        "consent_check",
                        "data_minimization",
                    ],
                },
                "right_to_erasure": {
                    "description": "Users must be able to request data deletion",
                    "checks": ["deletion_mechanism", "data_retention_policy"],
                },
            },
            ComplianceStandard.SOC2: {
                "access_control": {
                    "description": "Access controls must be implemented",
                    "checks": ["authentication_check", "authorization_check"],
                },
                "data_encryption": {
                    "description": "Sensitive data must be encrypted",
                    "checks": ["encryption_at_rest", "encryption_in_transit"],
                },
            },
            ComplianceStandard.PCI_DSS: {
                "cardholder_data_protection": {
                    "description": "Cardholder data must be protected",
                    "checks": ["pci_encryption_check", "access_restriction"],
                }
            },
            ComplianceStandard.HIPAA: {
                "phi_protection": {
                    "description": "Protected Health Information must be secured",
                    "checks": ["phi_encryption", "access_logging", "audit_trails"],
                }
            },
        }

    def check_compliance(
        self, code: str, plan: Plan, standards: List[ComplianceStandard]
    ) -> List[ComplianceCheck]:
        """Check code and plan for compliance with specified standards."""
        compliance_results = []

        for standard in standards:
            if standard in self.compliance_rules:
                standard_results = self._check_standard_compliance(code, plan, standard)
                compliance_results.extend(standard_results)

        return compliance_results

    def _check_standard_compliance(
        self, code: str, plan: Plan, standard: ComplianceStandard
    ) -> List[ComplianceCheck]:
        """Check compliance for a specific standard."""
        results = []
        rules = self.compliance_rules[standard]

        for requirement_id, rule_config in rules.items():
            for check_name in rule_config["checks"]:
                check_result = self._perform_compliance_check(
                    code, plan, check_name, standard, requirement_id, rule_config
                )
                results.append(check_result)

        return results

    def _perform_compliance_check(
        self,
        code: str,
        plan: Plan,
        check_name: str,
        standard: ComplianceStandard,
        requirement_id: str,
        rule_config: Dict,
    ) -> ComplianceCheck:
        """Perform a specific compliance check."""
        # Implementation of various compliance checks
        check_methods = {
            "encryption_check": self._check_encryption,
            "authentication_check": self._check_authentication,
            "authorization_check": self._check_authorization,
            "audit_trails": self._check_audit_trails,
            "data_minimization": self._check_data_minimization,
            "deletion_mechanism": self._check_deletion_mechanism,
            "consent_check": self._check_consent_mechanisms,
            "pci_encryption_check": self._check_pci_encryption,
            "phi_encryption": self._check_phi_encryption,
            "access_logging": self._check_access_logging,
        }

        if check_name in check_methods:
            status, details, evidence, remediation = check_methods[check_name](
                code, plan
            )
        else:
            status = "not_applicable"
            details = f"Check {check_name} not implemented"
            evidence = []
            remediation = []

        return ComplianceCheck(
            standard=standard,
            requirement_id=requirement_id,
            requirement_name=rule_config["description"],
            status=status,
            details=details,
            evidence=evidence,
            remediation_steps=remediation,
        )

    def _check_encryption(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for proper encryption implementation."""
        encryption_indicators = [
            "encrypt",
            "AES",
            "RSA",
            "TLS",
            "SSL",
            "bcrypt",
            "scrypt",
        ]
        weak_encryption = ["MD5", "SHA1", "DES", "RC4"]

        has_encryption = any(indicator in code for indicator in encryption_indicators)
        has_weak_encryption = any(weak in code for weak in weak_encryption)

        if has_weak_encryption:
            return (
                "fail",
                "Weak encryption algorithms detected",
                [],
                ["Replace weak encryption with strong algorithms"],
            )
        elif has_encryption:
            return (
                "pass",
                "Encryption mechanisms found",
                ["Modern encryption algorithms detected"],
                [],
            )
        else:
            return (
                "warning",
                "No encryption mechanisms detected",
                [],
                ["Implement encryption for sensitive data"],
            )

    def _check_authentication(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for authentication mechanisms."""
        auth_indicators = ["authenticate", "login", "password", "jwt", "oauth", "token"]

        has_auth = any(indicator in code.lower() for indicator in auth_indicators)

        if has_auth:
            return (
                "pass",
                "Authentication mechanisms found",
                ["Authentication code detected"],
                [],
            )
        else:
            return (
                "warning",
                "No authentication mechanisms detected",
                [],
                ["Implement proper authentication"],
            )

    def _check_authorization(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for authorization mechanisms."""
        authz_indicators = [
            "authorize",
            "permission",
            "role",
            "access_control",
            "rbac",
            "permissions",
        ]

        has_authz = any(indicator in code.lower() for indicator in authz_indicators)

        if has_authz:
            return (
                "pass",
                "Authorization mechanisms found",
                ["Authorization code detected"],
                [],
            )
        else:
            return (
                "warning",
                "No authorization mechanisms detected",
                [],
                ["Implement proper authorization"],
            )

    def _check_audit_trails(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for audit trail implementation."""
        audit_indicators = ["audit", "log", "track", "monitor", "event"]

        has_audit = any(indicator in code.lower() for indicator in audit_indicators)

        if has_audit:
            return "pass", "Audit trail mechanisms found", ["Logging code detected"], []
        else:
            return (
                "fail",
                "No audit trail mechanisms detected",
                [],
                ["Implement comprehensive audit logging"],
            )

    def _check_data_minimization(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for data minimization practices."""
        # This is a simplified check - would need more sophisticated analysis
        return (
            "not_applicable",
            "Data minimization requires manual review",
            [],
            ["Review data collection practices"],
        )

    def _check_deletion_mechanism(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for data deletion mechanisms."""
        deletion_indicators = ["delete", "remove", "purge", "cleanup"]

        has_deletion = any(
            indicator in code.lower() for indicator in deletion_indicators
        )

        if has_deletion:
            return (
                "pass",
                "Data deletion mechanisms found",
                ["Deletion code detected"],
                [],
            )
        else:
            return (
                "warning",
                "No data deletion mechanisms detected",
                [],
                ["Implement data deletion capabilities"],
            )

    def _check_consent_mechanisms(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for consent mechanisms."""
        consent_indicators = ["consent", "agree", "terms", "privacy", "gdpr"]

        has_consent = any(indicator in code.lower() for indicator in consent_indicators)

        if has_consent:
            return "pass", "Consent mechanisms found", ["Consent code detected"], []
        else:
            return (
                "warning",
                "No consent mechanisms detected",
                [],
                ["Implement consent collection"],
            )

    def _check_pci_encryption(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for PCI-compliant encryption."""
        return self._check_encryption(code, plan)

    def _check_phi_encryption(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for PHI encryption (HIPAA)."""
        return self._check_encryption(code, plan)

    def _check_access_logging(
        self, code: str, plan: Plan
    ) -> Tuple[str, str, List[str], List[str]]:
        """Check for access logging."""
        return self._check_audit_trails(code, plan)


class SecurityAnalyzer:
    """Main security analyzer class combining vulnerability detection and compliance checking."""

    def __init__(self):
        self.pattern_detector = SecurityPatternDetector()
        self.compliance_checker = ComplianceChecker()

    async def analyze_code_security(
        self, code: str, plan: Plan, filename: str = "unknown"
    ) -> SecurityReport:
        """Perform comprehensive security analysis on code."""
        scan_id = secrets.token_hex(8)
        timestamp = datetime.utcnow()
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        # Detect vulnerabilities
        vulnerabilities = self.pattern_detector.scan_code(code, filename)

        # Check compliance (default to common standards)
        compliance_standards = [ComplianceStandard.SOC2, ComplianceStandard.GDPR]
        compliance_status = self.compliance_checker.check_compliance(
            code, plan, compliance_standards
        )

        # Calculate security score
        security_score = self._calculate_security_score(
            vulnerabilities, compliance_status
        )

        # Generate recommendations
        recommendations = self._generate_security_recommendations(
            vulnerabilities, compliance_status
        )

        # Perform risk assessment
        risk_assessment = self._perform_risk_assessment(
            vulnerabilities, compliance_status, plan
        )

        # Create audit trail entry
        audit_trail = [
            {
                "action": "security_scan",
                "timestamp": timestamp.isoformat(),
                "scan_id": scan_id,
                "vulnerabilities_found": len(vulnerabilities),
                "compliance_checks": len(compliance_status),
            }
        ]

        return SecurityReport(
            scan_id=scan_id,
            timestamp=timestamp,
            code_hash=code_hash,
            vulnerabilities=vulnerabilities,
            compliance_status=compliance_status,
            security_score=security_score,
            recommendations=recommendations,
            risk_assessment=risk_assessment,
            audit_trail=audit_trail,
        )

    def _calculate_security_score(
        self,
        vulnerabilities: List[SecurityVulnerability],
        compliance_checks: List[ComplianceCheck],
    ) -> float:
        """Calculate overall security score (0-100)."""
        base_score = 100.0

        # Deduct points for vulnerabilities
        severity_penalties = {
            VulnerabilityLevel.CRITICAL: 25,
            VulnerabilityLevel.HIGH: 15,
            VulnerabilityLevel.MEDIUM: 8,
            VulnerabilityLevel.LOW: 3,
            VulnerabilityLevel.INFO: 1,
        }

        for vuln in vulnerabilities:
            penalty = severity_penalties.get(vuln.severity, 5)
            base_score -= penalty * vuln.confidence

        # Deduct points for compliance failures
        for check in compliance_checks:
            if check.status == "fail":
                base_score -= 10
            elif check.status == "warning":
                base_score -= 5

        return max(0.0, min(100.0, base_score))

    def _generate_security_recommendations(
        self,
        vulnerabilities: List[SecurityVulnerability],
        compliance_checks: List[ComplianceCheck],
    ) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []

        # Vulnerability-based recommendations
        critical_vulns = [
            v for v in vulnerabilities if v.severity == VulnerabilityLevel.CRITICAL
        ]
        if critical_vulns:
            recommendations.append(
                "Address critical security vulnerabilities immediately"
            )
            recommendations.append(
                "Implement automated security scanning in CI/CD pipeline"
            )

        high_vulns = [
            v for v in vulnerabilities if v.severity == VulnerabilityLevel.HIGH
        ]
        if high_vulns:
            recommendations.append("Review and fix high-severity security issues")

        # Check for common patterns
        vuln_types = {v.title for v in vulnerabilities}
        if any("injection" in vtype.lower() for vtype in vuln_types):
            recommendations.append(
                "Implement input validation and parameterized queries"
            )

        if any("credential" in vtype.lower() for vtype in vuln_types):
            recommendations.append(
                "Use secure credential management (environment variables, vaults)"
            )

        # Compliance-based recommendations
        failed_checks = [c for c in compliance_checks if c.status == "fail"]
        if failed_checks:
            recommendations.append(
                "Address compliance violations for regulatory requirements"
            )

        # General recommendations
        if len(vulnerabilities) > 10:
            recommendations.append(
                "Consider security code review and developer training"
            )

        recommendations.append(
            "Implement regular security assessments and penetration testing"
        )
        recommendations.append("Establish incident response procedures")

        return list(set(recommendations))  # Remove duplicates

    def _perform_risk_assessment(
        self,
        vulnerabilities: List[SecurityVulnerability],
        compliance_checks: List[ComplianceCheck],
        plan: Plan,
    ) -> Dict[str, Any]:
        """Perform comprehensive risk assessment."""
        risk_factors = []

        # Analyze vulnerability risks
        critical_count = len(
            [v for v in vulnerabilities if v.severity == VulnerabilityLevel.CRITICAL]
        )
        high_count = len(
            [v for v in vulnerabilities if v.severity == VulnerabilityLevel.HIGH]
        )

        if critical_count > 0:
            risk_factors.append(
                {
                    "category": "vulnerability",
                    "level": "critical",
                    "description": f"{critical_count} critical vulnerabilities found",
                    "impact": "high",
                    "likelihood": "high",
                }
            )

        if high_count > 3:
            risk_factors.append(
                {
                    "category": "vulnerability",
                    "level": "high",
                    "description": f"{high_count} high-severity vulnerabilities found",
                    "impact": "medium",
                    "likelihood": "medium",
                }
            )

        # Analyze compliance risks
        failed_compliance = [c for c in compliance_checks if c.status == "fail"]
        if failed_compliance:
            risk_factors.append(
                {
                    "category": "compliance",
                    "level": "high",
                    "description": f"{len(failed_compliance)} compliance requirements failed",
                    "impact": "high",
                    "likelihood": "high",
                }
            )

        # Calculate overall risk level
        if any(rf["level"] == "critical" for rf in risk_factors):
            overall_risk = "critical"
        elif any(rf["level"] == "high" for rf in risk_factors):
            overall_risk = "high"
        elif len(risk_factors) > 0:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        return {
            "overall_risk_level": overall_risk,
            "risk_factors": risk_factors,
            "mitigation_priority": (
                "immediate"
                if overall_risk == "critical"
                else "high" if overall_risk == "high" else "medium"
            ),
            "estimated_fix_time": self._estimate_fix_time(vulnerabilities),
            "business_impact": self._assess_business_impact(overall_risk, plan),
        }

    def _estimate_fix_time(self, vulnerabilities: List[SecurityVulnerability]) -> str:
        """Estimate time required to fix vulnerabilities."""
        critical_count = len(
            [v for v in vulnerabilities if v.severity == VulnerabilityLevel.CRITICAL]
        )
        high_count = len(
            [v for v in vulnerabilities if v.severity == VulnerabilityLevel.HIGH]
        )
        medium_count = len(
            [v for v in vulnerabilities if v.severity == VulnerabilityLevel.MEDIUM]
        )

        total_hours = critical_count * 8 + high_count * 4 + medium_count * 2

        if total_hours < 8:
            return "1 day"
        elif total_hours < 40:
            return f"{total_hours // 8 + 1} days"
        else:
            return f"{total_hours // 40 + 1} weeks"

    def _assess_business_impact(self, risk_level: str, plan: Plan) -> str:
        """Assess potential business impact of security risks."""
        impact_levels = {
            "critical": "Severe business disruption, potential data breach, regulatory fines",
            "high": "Significant operational impact, customer trust issues, compliance violations",
            "medium": "Moderate operational disruption, potential security incidents",
            "low": "Minor security concerns, best practice improvements needed",
        }

        return impact_levels.get(risk_level, "Unknown impact level")
