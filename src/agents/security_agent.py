"""Security Agent - Specializes in security analysis and vulnerability assessment."""

import asyncio
import re
from typing import Any, Dict, List
from datetime import datetime

from .base_agent import BaseAgent, AgentConfig, TaskInput


class SecurityAgent(BaseAgent):
    """Agent specialized in security analysis and vulnerability assessment."""

    @classmethod
    def create(cls, agent_id: str, name: str | None = None) -> "SecurityAgent":
        """Factory compatible with legacy startup scripts."""
        return cls(agent_id=agent_id, name=name)

    def __init__(self, agent_id: str = None, name: str = None, config: AgentConfig = None):
        if config is None:
            # Legacy initialization with individual parameters
            config = AgentConfig(
                agent_id=agent_id,
                agent_type="security",
                name=name or f"Security-{agent_id}",
                capabilities=[
                    "vulnerability_analysis",
                    "security_review",
                    "compliance_check",
                    "threat_modeling",
                    "penetration_testing",
                    "security_architecture",
                "authentication_review",
                "authorization_review",
                "data_protection_review",
                "security_audit",
            ],
            max_concurrent_tasks=4,
            heartbeat_interval=30,
        )
        super().__init__(config)

        # Security-specific knowledge base
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.compliance_frameworks = self._load_compliance_frameworks()
        self.security_best_practices = self._load_security_best_practices()

    async def _initialize_agent(self) -> None:
        """Initialize security-specific resources."""
        self.logger.info(
            "Security agent initialized with vulnerability patterns and compliance frameworks"
        )
        await asyncio.sleep(0.1)  # Agent initialization complete

    async def process_task(self, task: TaskInput) -> Dict[str, Any]:
        """Process security-related tasks."""
        task_type = task.task_type.lower()
        context = task.context

        if task_type == "vulnerability_scan":
            return await self._scan_vulnerabilities(context)
        elif task_type == "security_review":
            return await self._security_review(context)
        elif task_type == "compliance_check":
            return await self._compliance_check(context)
        elif task_type == "threat_model":
            return await self._create_threat_model(context)
        elif task_type == "security_audit":
            return await self._security_audit(context)
        elif task_type == "authentication_review":
            return await self._review_authentication(context)
        elif task_type == "authorization_review":
            return await self._review_authorization(context)
        elif task_type == "data_protection_review":
            return await self._review_data_protection(context)
        else:
            raise ValueError(f"Unknown security task type: {task_type}")

    async def get_capabilities(self) -> List[str]:
        """Get current security capabilities."""
        return self.config.capabilities

    async def _scan_vulnerabilities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Scan code or system for vulnerabilities."""
        code = context.get("code", "")
        language = context.get("language", "unknown")
        scan_type = context.get("scan_type", "comprehensive")

        vulnerabilities = []

        # Code-based vulnerability scanning
        if code:
            vulnerabilities.extend(
                await self._scan_code_vulnerabilities(code, language)
            )

        # Configuration-based scanning
        config_data = context.get("configuration", {})
        if config_data:
            vulnerabilities.extend(await self._scan_config_vulnerabilities(config_data))

        # Dependencies scanning
        dependencies = context.get("dependencies", [])
        if dependencies:
            vulnerabilities.extend(
                await self._scan_dependency_vulnerabilities(dependencies)
            )

        # Classify vulnerabilities by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "medium")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        risk_score = self._calculate_risk_score(vulnerabilities)

        return {
            "scan_type": scan_type,
            "language": language,
            "total_vulnerabilities": len(vulnerabilities),
            "severity_breakdown": severity_counts,
            "risk_score": risk_score,
            "vulnerabilities": vulnerabilities,
            "recommendations": await self._generate_vulnerability_recommendations(
                vulnerabilities
            ),
            "scan_timestamp": datetime.utcnow().isoformat(),
            "remediation_priority": await self._prioritize_remediation(vulnerabilities),
        }

    async def _security_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive security review."""
        context.get("system_description", "")
        architecture = context.get("architecture", {})
        context.get("code_components", [])

        review_areas = [
            "authentication",
            "authorization",
            "data_protection",
            "input_validation",
            "output_encoding",
            "session_management",
            "cryptography",
            "error_handling",
            "logging",
            "configuration",
        ]

        findings = []
        for area in review_areas:
            area_findings = await self._review_security_area(area, context)
            findings.extend(area_findings)

        # Architecture-specific review
        if architecture:
            arch_findings = await self._review_security_architecture(architecture)
            findings.extend(arch_findings)

        # Aggregate findings
        security_score = self._calculate_security_score(findings)

        return {
            "review_areas": review_areas,
            "total_findings": len(findings),
            "security_score": security_score,
            "findings": findings,
            "summary": self._generate_security_summary(findings),
            "action_items": await self._generate_security_action_items(findings),
            "compliance_status": await self._assess_compliance_status(findings),
            "review_timestamp": datetime.utcnow().isoformat(),
        }

    async def _compliance_check(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with security frameworks."""
        frameworks = context.get("frameworks", ["owasp", "nist"])
        system_info = context.get("system_info", {})

        compliance_results = {}

        for framework in frameworks:
            if framework.lower() in self.compliance_frameworks:
                result = await self._check_framework_compliance(framework, system_info)
                compliance_results[framework] = result

        # Overall compliance score
        total_checks = sum(
            len(result["checks"]) for result in compliance_results.values()
        )
        passed_checks = sum(
            len([c for c in result["checks"] if c["status"] == "pass"])
            for result in compliance_results.values()
        )

        overall_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        return {
            "frameworks_checked": frameworks,
            "overall_compliance_score": round(overall_score, 1),
            "compliance_results": compliance_results,
            "failed_requirements": await self._get_failed_requirements(
                compliance_results
            ),
            "remediation_plan": await self._create_compliance_remediation_plan(
                compliance_results
            ),
            "check_timestamp": datetime.utcnow().isoformat(),
        }

    async def _create_threat_model(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create threat model for the system."""
        system_description = context.get("system_description", "")
        assets = context.get("assets", [])
        entry_points = context.get("entry_points", [])
        trust_boundaries = context.get("trust_boundaries", [])

        # Identify threats using STRIDE methodology
        threats = []

        # Spoofing threats
        spoofing_threats = await self._identify_spoofing_threats(entry_points, assets)
        threats.extend(spoofing_threats)

        # Tampering threats
        tampering_threats = await self._identify_tampering_threats(
            assets, trust_boundaries
        )
        threats.extend(tampering_threats)

        # Repudiation threats
        repudiation_threats = await self._identify_repudiation_threats(assets)
        threats.extend(repudiation_threats)

        # Information disclosure threats
        disclosure_threats = await self._identify_disclosure_threats(
            assets, trust_boundaries
        )
        threats.extend(disclosure_threats)

        # Denial of service threats
        dos_threats = await self._identify_dos_threats(entry_points)
        threats.extend(dos_threats)

        # Elevation of privilege threats
        privilege_threats = await self._identify_privilege_threats(trust_boundaries)
        threats.extend(privilege_threats)

        # Risk assessment
        risk_matrix = self._create_risk_matrix(threats)

        return {
            "system_description": system_description,
            "assets": assets,
            "entry_points": entry_points,
            "trust_boundaries": trust_boundaries,
            "threats": threats,
            "threat_categories": {
                "spoofing": len(spoofing_threats),
                "tampering": len(tampering_threats),
                "repudiation": len(repudiation_threats),
                "information_disclosure": len(disclosure_threats),
                "denial_of_service": len(dos_threats),
                "elevation_of_privilege": len(privilege_threats),
            },
            "risk_matrix": risk_matrix,
            "high_priority_threats": [
                t for t in threats if t.get("risk_level") == "high"
            ],
            "mitigation_strategies": await self._generate_mitigation_strategies(
                threats
            ),
            "model_timestamp": datetime.utcnow().isoformat(),
        }

    async def _security_audit(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive security audit."""
        audit_scope = context.get("scope", "full")
        systems = context.get("systems", [])
        applications = context.get("applications", [])

        audit_results = {
            "infrastructure": await self._audit_infrastructure(systems),
            "applications": await self._audit_applications(applications),
            "policies": await self._audit_security_policies(
                context.get("policies", {})
            ),
            "procedures": await self._audit_security_procedures(
                context.get("procedures", {})
            ),
            "access_controls": await self._audit_access_controls(
                context.get("access_controls", {})
            ),
        }

        # Calculate overall audit score
        scores = [result.get("score", 0) for result in audit_results.values()]
        overall_score = sum(scores) / len(scores) if scores else 0

        # Identify critical issues
        critical_issues = []
        for area, result in audit_results.items():
            for issue in result.get("issues", []):
                if issue.get("severity") == "critical":
                    critical_issues.append({**issue, "area": area})

        return {
            "audit_scope": audit_scope,
            "overall_score": round(overall_score, 1),
            "audit_results": audit_results,
            "critical_issues": critical_issues,
            "improvement_recommendations": await self._generate_audit_recommendations(
                audit_results
            ),
            "next_audit_date": (
                datetime.utcnow().replace(month=datetime.utcnow().month + 6)
            ).isoformat(),
            "audit_timestamp": datetime.utcnow().isoformat(),
        }

    async def _review_authentication(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review authentication mechanisms."""
        auth_config = context.get("authentication", {})
        context.get("user_management", {})

        findings = []

        # Check authentication methods
        auth_methods = auth_config.get("methods", [])
        if "password" in auth_methods and "mfa" not in auth_methods:
            findings.append(
                {
                    "type": "weak_authentication",
                    "severity": "high",
                    "description": "Password-only authentication without MFA",
                    "recommendation": "Implement multi-factor authentication",
                }
            )

        # Check password policies
        password_policy = auth_config.get("password_policy", {})
        if not password_policy.get("min_length", 0) >= 12:
            findings.append(
                {
                    "type": "weak_password_policy",
                    "severity": "medium",
                    "description": "Password minimum length is too short",
                    "recommendation": "Set minimum password length to 12 characters",
                }
            )

        # Check session management
        session_config = auth_config.get("session", {})
        if not session_config.get("timeout"):
            findings.append(
                {
                    "type": "session_management",
                    "severity": "medium",
                    "description": "No session timeout configured",
                    "recommendation": "Implement appropriate session timeouts",
                }
            )

        score = max(0, 100 - (len(findings) * 15))

        return {
            "authentication_score": score,
            "findings": findings,
            "recommendations": [f["recommendation"] for f in findings],
            "compliant_features": self._identify_compliant_auth_features(auth_config),
            "review_timestamp": datetime.utcnow().isoformat(),
        }

    async def _review_authorization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review authorization mechanisms."""
        authz_config = context.get("authorization", {})
        roles = context.get("roles", [])
        permissions = context.get("permissions", [])

        findings = []

        # Check for role-based access control
        if not roles:
            findings.append(
                {
                    "type": "missing_rbac",
                    "severity": "high",
                    "description": "No role-based access control implemented",
                    "recommendation": "Implement role-based access control",
                }
            )

        # Check for principle of least privilege
        for role in roles:
            role_permissions = role.get("permissions", [])
            if len(role_permissions) > 20:  # Arbitrary threshold
                findings.append(
                    {
                        "type": "excessive_permissions",
                        "severity": "medium",
                        "description": f"Role '{role.get('name')}' has excessive permissions",
                        "recommendation": "Review and reduce role permissions",
                    }
                )

        # Check for proper access control implementation
        if not authz_config.get("default_deny", False):
            findings.append(
                {
                    "type": "default_allow",
                    "severity": "high",
                    "description": "Default allow policy detected",
                    "recommendation": "Implement default deny policy",
                }
            )

        score = max(0, 100 - (len(findings) * 20))

        return {
            "authorization_score": score,
            "findings": findings,
            "role_analysis": await self._analyze_roles(roles),
            "permission_analysis": await self._analyze_permissions(permissions),
            "recommendations": [f["recommendation"] for f in findings],
            "review_timestamp": datetime.utcnow().isoformat(),
        }

    async def _review_data_protection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review data protection mechanisms."""
        context.get("data_protection", {})
        encryption_config = context.get("encryption", {})
        backup_config = context.get("backup", {})

        findings = []

        # Check encryption at rest
        if not encryption_config.get("at_rest", False):
            findings.append(
                {
                    "type": "no_encryption_at_rest",
                    "severity": "high",
                    "description": "Data not encrypted at rest",
                    "recommendation": "Implement encryption at rest",
                }
            )

        # Check encryption in transit
        if not encryption_config.get("in_transit", False):
            findings.append(
                {
                    "type": "no_encryption_in_transit",
                    "severity": "critical",
                    "description": "Data not encrypted in transit",
                    "recommendation": "Implement TLS/SSL for all data transmission",
                }
            )

        # Check key management
        key_management = encryption_config.get("key_management", {})
        if not key_management.get("rotation", False):
            findings.append(
                {
                    "type": "no_key_rotation",
                    "severity": "medium",
                    "description": "No key rotation policy",
                    "recommendation": "Implement regular key rotation",
                }
            )

        # Check backup security
        if backup_config and not backup_config.get("encrypted", False):
            findings.append(
                {
                    "type": "unencrypted_backups",
                    "severity": "high",
                    "description": "Backups are not encrypted",
                    "recommendation": "Encrypt all backup data",
                }
            )

        score = max(0, 100 - (len(findings) * 18))

        return {
            "data_protection_score": score,
            "findings": findings,
            "encryption_status": self._assess_encryption_status(encryption_config),
            "compliance_gaps": await self._identify_data_protection_gaps(findings),
            "recommendations": [f["recommendation"] for f in findings],
            "review_timestamp": datetime.utcnow().isoformat(),
        }

    # Utility methods for vulnerability scanning

    async def _scan_code_vulnerabilities(
        self, code: str, language: str
    ) -> List[Dict[str, Any]]:
        """Scan code for vulnerabilities."""
        vulnerabilities = []

        # SQL Injection patterns
        sql_injection_patterns = [
            r"SELECT.*FROM.*WHERE.*['\"].*['\"]",
            r"INSERT.*INTO.*VALUES.*['\"].*['\"]",
            r"UPDATE.*SET.*WHERE.*['\"].*['\"]",
            r"DELETE.*FROM.*WHERE.*['\"].*['\"]",
        ]

        for pattern in sql_injection_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append(
                    {
                        "type": "sql_injection",
                        "severity": "high",
                        "description": "Potential SQL injection vulnerability",
                        "location": f"Line {code[:match.start()].count(chr(10)) + 1}",
                        "code_snippet": match.group(),
                        "recommendation": "Use parameterized queries",
                    }
                )

        # XSS patterns
        xss_patterns = [
            r"document\.write\s*\(",
            r"innerHTML\s*=",
            r"eval\s*\(",
            r"setTimeout\s*\(\s*['\"].*['\"]",
        ]

        for pattern in xss_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append(
                    {
                        "type": "xss",
                        "severity": "medium",
                        "description": "Potential XSS vulnerability",
                        "location": f"Line {code[:match.start()].count(chr(10)) + 1}",
                        "code_snippet": match.group(),
                        "recommendation": "Sanitize user input and use safe DOM manipulation",
                    }
                )

        # Hardcoded secrets
        secret_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]

        for pattern in secret_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append(
                    {
                        "type": "hardcoded_secret",
                        "severity": "critical",
                        "description": "Hardcoded secret detected",
                        "location": f"Line {code[:match.start()].count(chr(10)) + 1}",
                        "code_snippet": "***REDACTED***",
                        "recommendation": "Use environment variables or secure key management",
                    }
                )

        return vulnerabilities

    async def _scan_config_vulnerabilities(
        self, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Scan configuration for vulnerabilities."""
        vulnerabilities = []

        # Check for insecure configurations
        if config.get("debug", False):
            vulnerabilities.append(
                {
                    "type": "debug_enabled",
                    "severity": "medium",
                    "description": "Debug mode enabled in production",
                    "recommendation": "Disable debug mode in production",
                }
            )

        if not config.get("https", True):
            vulnerabilities.append(
                {
                    "type": "insecure_transport",
                    "severity": "high",
                    "description": "HTTPS not enforced",
                    "recommendation": "Enable HTTPS for all communications",
                }
            )

        # Check security headers
        security_headers = config.get("security_headers", {})
        required_headers = [
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
        ]

        for header in required_headers:
            if header not in security_headers:
                vulnerabilities.append(
                    {
                        "type": "missing_security_header",
                        "severity": "medium",
                        "description": f"Missing security header: {header}",
                        "recommendation": f"Add {header} security header",
                    }
                )

        return vulnerabilities

    async def _scan_dependency_vulnerabilities(
        self, dependencies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Scan dependencies for known vulnerabilities."""
        vulnerabilities = []

        # This would typically integrate with vulnerability databases
        # For now, we'll simulate some common vulnerable dependencies
        known_vulnerabilities = {
            "lodash": {
                "versions": ["<4.17.19"],
                "cve": "CVE-2020-8203",
                "severity": "high",
            },
            "moment": {
                "versions": ["<2.29.4"],
                "cve": "CVE-2022-31129",
                "severity": "high",
            },
            "axios": {
                "versions": ["<0.21.2"],
                "cve": "CVE-2021-3749",
                "severity": "medium",
            },
        }

        for dep in dependencies:
            name = dep.get("name", "")
            version = dep.get("version", "")

            if name in known_vulnerabilities:
                vuln_info = known_vulnerabilities[name]
                # Simplified version checking
                if any(
                    version.startswith(v.replace("<", "").replace("=", ""))
                    for v in vuln_info["versions"]
                ):
                    vulnerabilities.append(
                        {
                            "type": "vulnerable_dependency",
                            "severity": vuln_info["severity"],
                            "description": f"Vulnerable dependency: {name} {version}",
                            "cve": vuln_info["cve"],
                            "recommendation": f"Update {name} to latest version",
                        }
                    )

        return vulnerabilities

    def _calculate_risk_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score based on vulnerabilities."""
        severity_weights = {"critical": 10, "high": 7, "medium": 4, "low": 2, "info": 1}

        total_score = sum(
            severity_weights.get(v.get("severity", "medium"), 4)
            for v in vulnerabilities
        )

        # Normalize to 0-100 scale
        if not vulnerabilities:
            return 0.0

        max_possible = len(vulnerabilities) * 10
        return min(100.0, (total_score / max_possible) * 100)

    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        """Load vulnerability patterns for scanning."""
        return {
            "sql_injection": {
                "patterns": [
                    r"SELECT.*FROM.*WHERE.*['\"].*['\"]",
                    r"INSERT.*INTO.*VALUES.*['\"].*['\"]",
                ],
                "severity": "high",
            },
            "xss": {
                "patterns": [r"document\.write\s*\(", r"innerHTML\s*="],
                "severity": "medium",
            },
        }

    def _load_compliance_frameworks(self) -> Dict[str, Any]:
        """Load compliance framework definitions."""
        return {
            "owasp": {
                "name": "OWASP Top 10",
                "categories": [
                    "Injection",
                    "Broken Authentication",
                    "Sensitive Data Exposure",
                    "XML External Entities",
                    "Broken Access Control",
                    "Security Misconfiguration",
                    "Cross-Site Scripting",
                    "Insecure Deserialization",
                    "Using Components with Known Vulnerabilities",
                    "Insufficient Logging & Monitoring",
                ],
            },
            "nist": {
                "name": "NIST Cybersecurity Framework",
                "categories": ["Identify", "Protect", "Detect", "Respond", "Recover"],
            },
        }

    def _load_security_best_practices(self) -> Dict[str, Any]:
        """Load security best practices."""
        return {
            "authentication": [
                "Use multi-factor authentication",
                "Implement strong password policies",
                "Use secure session management",
            ],
            "authorization": [
                "Implement principle of least privilege",
                "Use role-based access control",
                "Regular access reviews",
            ],
            "data_protection": [
                "Encrypt data at rest and in transit",
                "Implement proper key management",
                "Regular backup and recovery testing",
            ],
        }

    # Additional utility methods would be implemented here for the remaining functionality
    # This includes methods for threat modeling, compliance checking, auditing, etc.

    async def _generate_vulnerability_recommendations(
        self, vulnerabilities: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on found vulnerabilities."""
        recommendations = []

        # Group by type and provide specific recommendations
        vuln_types = set(v.get("type") for v in vulnerabilities)

        if "sql_injection" in vuln_types:
            recommendations.append(
                "Implement parameterized queries and input validation"
            )

        if "xss" in vuln_types:
            recommendations.append(
                "Implement output encoding and Content Security Policy"
            )

        if "hardcoded_secret" in vuln_types:
            recommendations.append("Move secrets to secure configuration management")

        return recommendations

    async def _prioritize_remediation(
        self, vulnerabilities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prioritize vulnerability remediation."""
        # Sort by severity and impact
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

        sorted_vulns = sorted(
            vulnerabilities,
            key=lambda v: severity_order.get(v.get("severity", "medium"), 2),
        )

        priority_list = []
        for i, vuln in enumerate(sorted_vulns[:10]):  # Top 10
            priority_list.append(
                {
                    "priority": i + 1,
                    "type": vuln.get("type"),
                    "severity": vuln.get("severity"),
                    "description": vuln.get("description"),
                    "estimated_effort": self._estimate_remediation_effort(vuln),
                }
            )

        return priority_list

    def _estimate_remediation_effort(self, vulnerability: Dict[str, Any]) -> str:
        """Estimate effort required to fix vulnerability."""
        vuln_type = vulnerability.get("type", "")
        severity = vulnerability.get("severity", "medium")

        effort_map = {
            ("sql_injection", "high"): "2-4 hours",
            ("xss", "medium"): "1-2 hours",
            ("hardcoded_secret", "critical"): "30 minutes",
            ("missing_security_header", "medium"): "15 minutes",
        }

        return effort_map.get((vuln_type, severity), "1-3 hours")

    # Additional agent methods for comprehensive functionality
    async def _review_security_area(
        self, area: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Review specific security area."""
        return []  # Implementation would be specific to each area

    async def _review_security_architecture(
        self, architecture: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Review security architecture."""
        return []  # Implementation would analyze architecture patterns

    def _calculate_security_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate overall security score."""
        if not findings:
            return 95.0  # High score if no findings

        severity_impact = {
            "critical": 20,
            "high": 15,
            "medium": 10,
            "low": 5,
            "info": 2,
        }

        total_impact = sum(
            severity_impact.get(f.get("severity", "medium"), 10) for f in findings
        )
        return max(0, 100 - total_impact)

    def _generate_security_summary(self, findings: List[Dict[str, Any]]) -> str:
        """Generate summary of security review."""
        if not findings:
            return "No significant security issues identified"

        critical_count = len([f for f in findings if f.get("severity") == "critical"])
        high_count = len([f for f in findings if f.get("severity") == "high"])

        if critical_count > 0:
            return f"Critical security issues found ({critical_count}). Immediate action required."
        elif high_count > 0:
            return f"High severity issues found ({high_count}). Priority remediation needed."
        else:
            return "Medium and low severity issues identified. Regular remediation recommended."

    async def _generate_security_action_items(
        self, findings: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable security items."""
        action_items = []

        for finding in findings[:5]:  # Top 5 findings
            action_items.append(
                f"Address {finding.get('type', 'security issue')}: {finding.get('recommendation', 'Review and remediate')}"
            )

        return action_items

    async def _assess_compliance_status(
        self, findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess compliance status based on findings."""
        return {
            "overall_status": "partial" if findings else "compliant",
            "issues_count": len(findings),
            "priority_issues": [
                f for f in findings if f.get("severity") in ["critical", "high"]
            ],
        }
