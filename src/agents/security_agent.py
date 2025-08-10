"""Security Agent - specializes in security analysis and assessment."""

import asyncio
import re
from datetime import datetime
from typing import Any, Dict, List

from .base_agent import AgentConfig, BaseAgent, TaskInput


class SecurityAgent(BaseAgent):
    """Agent specialized in security analysis and vulnerability assessment."""

    @classmethod
    def create(cls, agent_id: str, name: str | None = None) -> "SecurityAgent":
        """Factory compatible with legacy startup scripts."""
        return cls(agent_id=agent_id, name=name)

    def __init__(
        self, agent_id: str | None = None, name: str | None = None, config: AgentConfig | None = None
    ):
        if config is None:
            config = AgentConfig(
                agent_id=agent_id or "security-unknown",
                agent_type="security",
                name=name or f"Security-{agent_id}",
                capabilities=[
                    "vulnerability_scan",
                    "security_review",
                    "compliance_check",
                ],
                max_concurrent_tasks=4,
                heartbeat_interval=30,
            )
        super().__init__(config)

        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.compliance_frameworks = self._load_compliance_frameworks()
        self.security_best_practices = self._load_security_best_practices()

    async def _initialize_agent(self) -> None:
        """Initialize security-specific resources."""
        self.logger.info("Security agent initialized and ready")
        await asyncio.sleep(0)  # Yield once

    async def process_task(self, task: TaskInput) -> Dict[str, Any]:
        """Process security-related tasks."""
        task_type = task.task_type.lower()
        ctx = task.context

        if task_type == "vulnerability_scan":
            return await self._scan_vulnerabilities(ctx)
        if task_type == "security_review":
            return await self._security_review(ctx)
        if task_type == "compliance_check":
            return await self._compliance_check(ctx)

        raise ValueError(f"Unknown security task type: {task_type}")

    async def get_capabilities(self) -> List[str]:
        return list(self.config.capabilities)

    async def _scan_vulnerabilities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Scan code, config, and dependencies for issues."""
        code = context.get("code", "")
        language = context.get("language", "unknown")
        dependencies = context.get("dependencies", [])
        configuration = context.get("configuration", {})

        vulns: List[Dict[str, Any]] = []
        if code:
            vulns.extend(await self._scan_code_vulnerabilities(code, language))
        if configuration:
            vulns.extend(await self._scan_config_vulnerabilities(configuration))
        if dependencies:
            vulns.extend(await self._scan_dependency_vulnerabilities(dependencies))

        severity_counts: Dict[str, int] = {k: 0 for k in ["critical", "high", "medium", "low", "info"]}
        for v in vulns:
            sev = v.get("severity", "medium")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "language": language,
            "total_vulnerabilities": len(vulns),
            "severity_breakdown": severity_counts,
            "risk_score": self._calculate_risk_score(vulns),
            "vulnerabilities": vulns,
            "scan_timestamp": datetime.utcnow().isoformat(),
        }

    async def _security_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a basic security review across core areas."""
        architecture = context.get("architecture", {})
        review_areas = [
            "authentication",
            "authorization",
            "data_protection",
            "input_validation",
            "logging",
            "configuration",
        ]

        findings: List[Dict[str, Any]] = []
        for area in review_areas:
            findings.extend(await self._review_security_area(area, context))

        if architecture:
            findings.extend(await self._review_security_architecture(architecture))

        score = self._calculate_security_score(findings)
        return {
            "review_areas": review_areas,
            "total_findings": len(findings),
            "security_score": score,
            "findings": findings,
            "summary": self._generate_security_summary(findings),
            "review_timestamp": datetime.utcnow().isoformat(),
        }

    async def _compliance_check(self, context: Dict[str, Any]) -> Dict[str, Any]:
        frameworks = context.get("frameworks", ["owasp", "nist"])
        system_info = context.get("system_info", {})
        results: Dict[str, Any] = {}
        for fw in frameworks:
            if fw.lower() in self.compliance_frameworks:
                results[fw] = await self._check_framework_compliance(fw, system_info)

        total = sum(len(r["checks"]) for r in results.values()) or 1
        passed = sum(
            sum(1 for c in r["checks"] if c["status"] == "pass") for r in results.values()
        )
        return {
            "frameworks_checked": frameworks,
            "overall_compliance_score": round(passed / total * 100, 1),
            "compliance_results": results,
            "check_timestamp": datetime.utcnow().isoformat(),
        }

    # === Helper implementations ===
    async def _scan_code_vulnerabilities(self, code: str, language: str) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        for name, pattern_info in self.vulnerability_patterns.items():
            for pattern in pattern_info.get("patterns", []):
                for match in re.finditer(pattern, code, re.IGNORECASE):
                    findings.append(
                        {
                            "type": name,
                            "severity": pattern_info.get("severity", "medium"),
                            "location": f"Line {code[:match.start()].count(chr(10)) + 1}",
                            "recommendation": pattern_info.get("recommendation", "Review usage"),
                        }
                    )
        return findings

    async def _scan_config_vulnerabilities(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        if config.get("debug") is True:
            findings.append(
                {
                    "type": "debug_enabled",
                    "severity": "medium",
                    "description": "Debug mode enabled",
                    "recommendation": "Disable debug in production",
                }
            )
        if not config.get("https", True):
            findings.append(
                {
                    "type": "insecure_transport",
                    "severity": "high",
                    "description": "HTTPS not enforced",
                    "recommendation": "Require TLS for all endpoints",
                }
            )
        return findings

    async def _scan_dependency_vulnerabilities(self, deps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        known = {
            "lodash": {"versions": ["<4.17.19"], "cve": "CVE-2020-8203", "severity": "high"},
            "axios": {"versions": ["<0.21.2"], "cve": "CVE-2021-3749", "severity": "medium"},
        }
        findings: List[Dict[str, Any]] = []
        for dep in deps:
            name = dep.get("name", "")
            version = dep.get("version", "")
            if name in known and version:
                info = known[name]
                for spec in info["versions"]:
                    if version.startswith(spec.replace("<", "").replace("=", "")):
                        findings.append(
                            {
                                "type": "vulnerable_dependency",
                                "severity": info["severity"],
                                "description": f"{name} {version} matches {spec}",
                                "cve": info["cve"],
                                "recommendation": f"Upgrade {name}",
                            }
                        )
        return findings

    def _calculate_risk_score(self, vulns: List[Dict[str, Any]]) -> float:
        weights = {"critical": 10, "high": 7, "medium": 4, "low": 2, "info": 1}
        if not vulns:
            return 0.0
        score = sum(weights.get(v.get("severity", "medium"), 4) for v in vulns)
        return min(100.0, (score / (len(vulns) * 10)) * 100)

    async def _review_security_area(self, area: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        checks: Dict[str, List[str]] = {
            "authentication": ["mfa_enabled", "password_policy"],
            "authorization": ["rbac", "least_privilege"],
            "data_protection": ["encryption_at_rest", "tls_enabled"],
            "input_validation": ["sanitize_inputs"],
            "logging": ["audit_logs"],
            "configuration": ["secure_headers"],
        }
        findings: List[Dict[str, Any]] = []
        conf = context.get(area, {})
        for check in checks.get(area, []):
            if not conf.get(check, False):
                findings.append(
                    {
                        "area": area,
                        "check": check,
                        "severity": "medium",
                        "description": f"Missing or disabled: {check}",
                        "recommendation": f"Enable or implement {check}",
                    }
                )
        return findings

    async def _review_security_architecture(self, architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        if not architecture.get("segmented_network", False):
            findings.append(
                {
                    "area": "architecture",
                    "check": "network_segmentation",
                    "severity": "medium",
                    "description": "Flat network topology",
                    "recommendation": "Introduce network segmentation",
                }
            )
        return findings

    def _calculate_security_score(self, findings: List[Dict[str, Any]]) -> float:
        penalty = sum(20 if f.get("severity") == "critical" else 10 if f.get("severity") == "high" else 5 for f in findings)
        return max(0.0, 100.0 - penalty)

    def _generate_security_summary(self, findings: List[Dict[str, Any]]) -> str:
        if not findings:
            return "No security issues detected"
        return f"Identified {len(findings)} potential security gaps"

    async def _check_framework_compliance(self, framework: str, system_info: Dict[str, Any]) -> Dict[str, Any]:
        checks = [
            {"id": "auth_mfa", "status": "pass" if system_info.get("mfa") else "fail"},
            {"id": "tls_enabled", "status": "pass" if system_info.get("tls") else "fail"},
            {"id": "logging_audit", "status": "pass" if system_info.get("audit_logs") else "fail"},
        ]
        score = round(100 * sum(1 for c in checks if c["status"] == "pass") / len(checks), 1)
        return {"framework": framework, "score": score, "checks": checks}

    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        return {
            "sql_injection": {
                "patterns": [r"SELECT.*FROM.*WHERE.*['\"][^'\"]+['\"]"],
                "severity": "high",
                "recommendation": "Use parameterized queries",
            },
            "xss": {
                "patterns": [r"document\\.write\\s*\\(", r"innerHTML\\s*="],
                "severity": "medium",
                "recommendation": "Sanitize and encode outputs",
            },
            "hardcoded_secret": {
                "patterns": [r"(password|api_key|secret|token)\s*=\s*['\"][^'\"]+['\"]"],
                "severity": "critical",
                "recommendation": "Use secret manager or env vars",
            },
        }

    def _load_compliance_frameworks(self) -> Dict[str, Any]:
        return {"owasp": {}, "nist": {}}

    def _load_security_best_practices(self) -> Dict[str, Any]:
        return {"password_policy": {"min_length": 12}}

