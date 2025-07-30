"""
Compliance and Regulatory Reporting System

Provides comprehensive compliance monitoring and reporting for various standards:
- GDPR (General Data Protection Regulation)
- HIPAA (Health Insurance Portability and Accountability Act)
- SOC 2 (Service Organization Control 2)
- PCI DSS (Payment Card Industry Data Security Standard)
- ISO 27001 (Information Security Management)
- NIST Cybersecurity Framework
- Custom compliance frameworks
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid

from jinja2 import Template
from fastapi import FastAPI, HTTPException
from fpdf import FPDF
import pandas as pd

from ..common.redis_client import RedisClient
from .audit_logging import AuditLogger, AuditEventType
from .vulnerability_scanner import VulnerabilityManager
from .session_management import SessionManager
from .encryption import EncryptionService

logger = logging.getLogger(__name__)


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks"""

    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    NIST_CSF = "nist_csf"
    CUSTOM = "custom"


class ComplianceStatus(str, Enum):
    """Compliance status values"""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_ASSESSED = "not_assessed"
    IN_PROGRESS = "in_progress"


class RiskLevel(str, Enum):
    """Risk levels for compliance issues"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceRequirement:
    """Represents a compliance requirement"""

    requirement_id: str
    framework: ComplianceFramework
    category: str
    title: str
    description: str
    control_objective: str
    implementation_guidance: str
    validation_criteria: List[str]
    risk_level: RiskLevel
    mandatory: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "requirement_id": self.requirement_id,
            "framework": self.framework.value,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "control_objective": self.control_objective,
            "implementation_guidance": self.implementation_guidance,
            "validation_criteria": self.validation_criteria,
            "risk_level": self.risk_level.value,
            "mandatory": self.mandatory,
        }


@dataclass
class ComplianceAssessment:
    """Results of compliance assessment"""

    assessment_id: str
    requirement_id: str
    framework: ComplianceFramework
    status: ComplianceStatus
    assessed_at: datetime
    assessed_by: str
    evidence: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    remediation_plan: Optional[str] = None
    next_assessment_due: Optional[datetime] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "assessment_id": self.assessment_id,
            "requirement_id": self.requirement_id,
            "framework": self.framework.value,
            "status": self.status.value,
            "assessed_at": self.assessed_at.isoformat(),
            "assessed_by": self.assessed_by,
            "evidence": self.evidence,
            "findings": self.findings,
            "remediation_plan": self.remediation_plan,
            "next_assessment_due": (
                self.next_assessment_due.isoformat()
                if self.next_assessment_due
                else None
            ),
            "notes": self.notes,
        }


@dataclass
class ComplianceReport:
    """Compliance report data"""

    report_id: str
    framework: ComplianceFramework
    generated_at: datetime
    generated_by: str
    period_start: datetime
    period_end: datetime
    overall_status: ComplianceStatus
    assessments: List[ComplianceAssessment]
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "framework": self.framework.value,
            "generated_at": self.generated_at.isoformat(),
            "generated_by": self.generated_by,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "overall_status": self.overall_status.value,
            "assessments": [a.to_dict() for a in self.assessments],
            "summary_metrics": self.summary_metrics,
            "recommendations": self.recommendations,
        }


class ComplianceRequirementRegistry:
    """Registry of compliance requirements for different frameworks"""

    def __init__(self):
        self.requirements: Dict[ComplianceFramework, List[ComplianceRequirement]] = {}
        self._initialize_requirements()

    def _initialize_requirements(self):
        """Initialize requirements for supported frameworks"""
        self._initialize_gdpr_requirements()
        self._initialize_hipaa_requirements()
        self._initialize_soc2_requirements()
        self._initialize_pci_dss_requirements()

    def _initialize_gdpr_requirements(self):
        """Initialize GDPR requirements"""
        gdpr_requirements = [
            ComplianceRequirement(
                requirement_id="gdpr_art_6",
                framework=ComplianceFramework.GDPR,
                category="lawful_basis",
                title="Lawful Basis for Processing",
                description="Processing of personal data must have a lawful basis",
                control_objective="Ensure all data processing has valid legal grounds",
                implementation_guidance="Document lawful basis for each processing activity",
                validation_criteria=[
                    "Record of Processing Activities (ROPA) exists",
                    "Lawful basis documented for each processing purpose",
                    "Consent mechanisms implemented where applicable",
                ],
                risk_level=RiskLevel.HIGH,
            ),
            ComplianceRequirement(
                requirement_id="gdpr_art_25",
                framework=ComplianceFramework.GDPR,
                category="data_protection_by_design",
                title="Data Protection by Design and Default",
                description="Implement data protection measures from the outset",
                control_objective="Integrate privacy protection into system design",
                implementation_guidance="Implement privacy-enhancing technologies and default privacy settings",
                validation_criteria=[
                    "Privacy impact assessments conducted",
                    "Default privacy settings implemented",
                    "Data minimization principles applied",
                ],
                risk_level=RiskLevel.HIGH,
            ),
            ComplianceRequirement(
                requirement_id="gdpr_art_32",
                framework=ComplianceFramework.GDPR,
                category="security",
                title="Security of Processing",
                description="Implement appropriate technical and organizational measures",
                control_objective="Ensure confidentiality, integrity, and availability of personal data",
                implementation_guidance="Implement encryption, access controls, and monitoring",
                validation_criteria=[
                    "Encryption at rest and in transit",
                    "Access control mechanisms",
                    "Security monitoring and logging",
                    "Regular security testing",
                ],
                risk_level=RiskLevel.CRITICAL,
            ),
            ComplianceRequirement(
                requirement_id="gdpr_art_33",
                framework=ComplianceFramework.GDPR,
                category="breach_notification",
                title="Notification of Data Breach",
                description="Report data breaches to supervisory authorities within 72 hours",
                control_objective="Ensure timely breach notification and response",
                implementation_guidance="Establish breach detection and notification procedures",
                validation_criteria=[
                    "Breach detection procedures documented",
                    "Notification templates prepared",
                    "72-hour notification process tested",
                ],
                risk_level=RiskLevel.HIGH,
            ),
        ]
        self.requirements[ComplianceFramework.GDPR] = gdpr_requirements

    def _initialize_hipaa_requirements(self):
        """Initialize HIPAA requirements"""
        hipaa_requirements = [
            ComplianceRequirement(
                requirement_id="hipaa_164.308",
                framework=ComplianceFramework.HIPAA,
                category="administrative_safeguards",
                title="Administrative Safeguards",
                description="Implement administrative actions to protect ePHI",
                control_objective="Establish administrative controls for ePHI protection",
                implementation_guidance="Assign security responsibilities and conduct training",
                validation_criteria=[
                    "Security officer appointed",
                    "Workforce training completed",
                    "Access management procedures",
                ],
                risk_level=RiskLevel.HIGH,
            ),
            ComplianceRequirement(
                requirement_id="hipaa_164.312",
                framework=ComplianceFramework.HIPAA,
                category="technical_safeguards",
                title="Technical Safeguards",
                description="Use technology to protect ePHI",
                control_objective="Implement technical controls for ePHI access and transmission",
                implementation_guidance="Implement access controls, audit controls, and encryption",
                validation_criteria=[
                    "Unique user identification",
                    "Audit logs implemented",
                    "Encryption for data transmission",
                ],
                risk_level=RiskLevel.CRITICAL,
            ),
        ]
        self.requirements[ComplianceFramework.HIPAA] = hipaa_requirements

    def _initialize_soc2_requirements(self):
        """Initialize SOC 2 requirements"""
        soc2_requirements = [
            ComplianceRequirement(
                requirement_id="soc2_cc1",
                framework=ComplianceFramework.SOC2,
                category="control_environment",
                title="Control Environment",
                description="Organization demonstrates commitment to integrity and ethical values",
                control_objective="Establish control environment foundation",
                implementation_guidance="Document policies, procedures, and governance structure",
                validation_criteria=[
                    "Code of conduct established",
                    "Organizational structure documented",
                    "Authority and responsibility assigned",
                ],
                risk_level=RiskLevel.MEDIUM,
            ),
            ComplianceRequirement(
                requirement_id="soc2_cc6",
                framework=ComplianceFramework.SOC2,
                category="logical_access",
                title="Logical and Physical Access Controls",
                description="Restrict logical and physical access to systems and data",
                control_objective="Control access to systems and data",
                implementation_guidance="Implement authentication, authorization, and monitoring",
                validation_criteria=[
                    "User access reviews performed",
                    "Multi-factor authentication implemented",
                    "Access logs monitored",
                ],
                risk_level=RiskLevel.HIGH,
            ),
        ]
        self.requirements[ComplianceFramework.SOC2] = soc2_requirements

    def _initialize_pci_dss_requirements(self):
        """Initialize PCI DSS requirements"""
        pci_requirements = [
            ComplianceRequirement(
                requirement_id="pci_req_3",
                framework=ComplianceFramework.PCI_DSS,
                category="data_protection",
                title="Protect Stored Cardholder Data",
                description="Protect cardholder data with strong cryptography",
                control_objective="Ensure cardholder data is protected at rest",
                implementation_guidance="Implement strong encryption and key management",
                validation_criteria=[
                    "Cardholder data encrypted with strong cryptography",
                    "Encryption keys properly managed",
                    "Data retention policies implemented",
                ],
                risk_level=RiskLevel.CRITICAL,
            ),
            ComplianceRequirement(
                requirement_id="pci_req_8",
                framework=ComplianceFramework.PCI_DSS,
                category="access_control",
                title="Identify and Authenticate Access",
                description="Assign unique ID to each person with computer access",
                control_objective="Ensure proper user identification and authentication",
                implementation_guidance="Implement unique user IDs and strong authentication",
                validation_criteria=[
                    "Unique user IDs assigned",
                    "Strong passwords enforced",
                    "Multi-factor authentication implemented",
                ],
                risk_level=RiskLevel.HIGH,
            ),
        ]
        self.requirements[ComplianceFramework.PCI_DSS] = pci_requirements

    def get_requirements(
        self, framework: ComplianceFramework
    ) -> List[ComplianceRequirement]:
        """Get requirements for a specific framework"""
        return self.requirements.get(framework, [])

    def get_requirement(
        self, framework: ComplianceFramework, requirement_id: str
    ) -> Optional[ComplianceRequirement]:
        """Get specific requirement"""
        requirements = self.get_requirements(framework)
        return next(
            (req for req in requirements if req.requirement_id == requirement_id), None
        )


class AutomatedComplianceChecker:
    """Automatically checks compliance against system state"""

    def __init__(
        self,
        redis_client: RedisClient,
        audit_logger: AuditLogger,
        vulnerability_manager: Optional[VulnerabilityManager] = None,
        session_manager: Optional[SessionManager] = None,
        encryption_service: Optional[EncryptionService] = None,
    ):
        self.redis_client = redis_client
        self.audit_logger = audit_logger
        self.vulnerability_manager = vulnerability_manager
        self.session_manager = session_manager
        self.encryption_service = encryption_service

        # Checker functions for different requirements
        self.checkers: Dict[str, Callable] = {}
        self._register_checkers()

    def _register_checkers(self):
        """Register automated checkers for compliance requirements"""
        # GDPR checkers
        self.checkers["gdpr_art_32"] = self._check_gdpr_security_measures
        self.checkers["gdpr_art_25"] = self._check_gdpr_data_protection_by_design

        # HIPAA checkers
        self.checkers["hipaa_164.312"] = self._check_hipaa_technical_safeguards

        # SOC 2 checkers
        self.checkers["soc2_cc6"] = self._check_soc2_access_controls

        # PCI DSS checkers
        self.checkers["pci_req_3"] = self._check_pci_data_protection
        self.checkers["pci_req_8"] = self._check_pci_access_control

    async def check_requirement(
        self, requirement: ComplianceRequirement
    ) -> ComplianceAssessment:
        """Automatically check a compliance requirement"""
        checker = self.checkers.get(requirement.requirement_id)

        if not checker:
            # Default assessment for requirements without automated checkers
            return ComplianceAssessment(
                assessment_id=str(uuid.uuid4()),
                requirement_id=requirement.requirement_id,
                framework=requirement.framework,
                status=ComplianceStatus.NOT_ASSESSED,
                assessed_at=datetime.utcnow(),
                assessed_by="automated_checker",
                notes="No automated checker available for this requirement",
            )

        try:
            return await checker(requirement)
        except Exception as e:
            logger.error(
                f"Error checking requirement {requirement.requirement_id}: {e}"
            )
            return ComplianceAssessment(
                assessment_id=str(uuid.uuid4()),
                requirement_id=requirement.requirement_id,
                framework=requirement.framework,
                status=ComplianceStatus.NOT_ASSESSED,
                assessed_at=datetime.utcnow(),
                assessed_by="automated_checker",
                notes=f"Checker failed: {str(e)}",
            )

    async def _check_gdpr_security_measures(
        self, requirement: ComplianceRequirement
    ) -> ComplianceAssessment:
        """Check GDPR Article 32 - Security of Processing"""
        evidence = []
        findings = []
        status = ComplianceStatus.COMPLIANT

        # Check encryption implementation
        if self.encryption_service:
            evidence.append("Encryption service is implemented")
        else:
            findings.append("No encryption service detected")
            status = ComplianceStatus.NON_COMPLIANT

        # Check vulnerability management
        if self.vulnerability_manager:
            vuln_summary = await self.vulnerability_manager.get_vulnerability_summary()
            critical_vulns = vuln_summary.get("by_severity", {}).get("critical", 0)
            high_vulns = vuln_summary.get("by_severity", {}).get("high", 0)

            if critical_vulns == 0 and high_vulns <= 5:
                evidence.append(
                    f"Vulnerability management active: {critical_vulns} critical, {high_vulns} high severity vulnerabilities"
                )
            else:
                findings.append(
                    f"High vulnerability count: {critical_vulns} critical, {high_vulns} high severity"
                )
                status = ComplianceStatus.PARTIALLY_COMPLIANT

        # Check session management
        if self.session_manager:
            evidence.append("Secure session management implemented")
        else:
            findings.append("No secure session management detected")
            status = ComplianceStatus.PARTIALLY_COMPLIANT

        return ComplianceAssessment(
            assessment_id=str(uuid.uuid4()),
            requirement_id=requirement.requirement_id,
            framework=requirement.framework,
            status=status,
            assessed_at=datetime.utcnow(),
            assessed_by="automated_checker",
            evidence=evidence,
            findings=findings,
            next_assessment_due=datetime.utcnow() + timedelta(days=90),
        )

    async def _check_gdpr_data_protection_by_design(
        self, requirement: ComplianceRequirement
    ) -> ComplianceAssessment:
        """Check GDPR Article 25 - Data Protection by Design"""
        evidence = []
        findings = []
        status = ComplianceStatus.PARTIALLY_COMPLIANT

        # Check if encryption is enabled by default
        if self.encryption_service:
            evidence.append("Encryption enabled by design")
        else:
            findings.append("No default encryption implementation")

        # Check session security defaults
        if self.session_manager:
            evidence.append("Secure session defaults implemented")
        else:
            findings.append("No secure session defaults")

        # Default to partially compliant as full assessment requires manual review
        return ComplianceAssessment(
            assessment_id=str(uuid.uuid4()),
            requirement_id=requirement.requirement_id,
            framework=requirement.framework,
            status=status,
            assessed_at=datetime.utcnow(),
            assessed_by="automated_checker",
            evidence=evidence,
            findings=findings,
            notes="Partial automated assessment - requires manual review for complete evaluation",
        )

    async def _check_hipaa_technical_safeguards(
        self, requirement: ComplianceRequirement
    ) -> ComplianceAssessment:
        """Check HIPAA Technical Safeguards"""
        evidence = []
        findings = []
        status = ComplianceStatus.COMPLIANT

        # Check audit controls
        evidence.append("Audit logging system implemented")

        # Check access controls
        if self.session_manager:
            evidence.append("User authentication and session management implemented")
        else:
            findings.append("No session management system detected")
            status = ComplianceStatus.NON_COMPLIANT

        # Check encryption
        if self.encryption_service:
            evidence.append("Encryption capabilities implemented")
        else:
            findings.append("No encryption service detected")
            status = ComplianceStatus.NON_COMPLIANT

        return ComplianceAssessment(
            assessment_id=str(uuid.uuid4()),
            requirement_id=requirement.requirement_id,
            framework=requirement.framework,
            status=status,
            assessed_at=datetime.utcnow(),
            assessed_by="automated_checker",
            evidence=evidence,
            findings=findings,
        )

    async def _check_soc2_access_controls(
        self, requirement: ComplianceRequirement
    ) -> ComplianceAssessment:
        """Check SOC 2 Access Controls"""
        evidence = []
        findings = []
        status = ComplianceStatus.COMPLIANT

        if self.session_manager:
            session_stats = await self.session_manager.get_session_statistics()
            evidence.append(
                f"Session management active with {session_stats.get('active_sessions', 0)} active sessions"
            )

            # Check for anomalous sessions
            anomalous = session_stats.get("anomalous_sessions", 0)
            if anomalous > 0:
                findings.append(f"{anomalous} anomalous sessions detected")
                status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            findings.append("No access control system detected")
            status = ComplianceStatus.NON_COMPLIANT

        return ComplianceAssessment(
            assessment_id=str(uuid.uuid4()),
            requirement_id=requirement.requirement_id,
            framework=requirement.framework,
            status=status,
            assessed_at=datetime.utcnow(),
            assessed_by="automated_checker",
            evidence=evidence,
            findings=findings,
        )

    async def _check_pci_data_protection(
        self, requirement: ComplianceRequirement
    ) -> ComplianceAssessment:
        """Check PCI DSS Data Protection"""
        evidence = []
        findings = []
        status = ComplianceStatus.NOT_ASSESSED

        if self.encryption_service:
            evidence.append("Encryption service available for data protection")
            status = ComplianceStatus.PARTIALLY_COMPLIANT
            findings.append(
                "Manual verification required for cardholder data encryption"
            )
        else:
            findings.append("No encryption service detected")
            status = ComplianceStatus.NON_COMPLIANT

        return ComplianceAssessment(
            assessment_id=str(uuid.uuid4()),
            requirement_id=requirement.requirement_id,
            framework=requirement.framework,
            status=status,
            assessed_at=datetime.utcnow(),
            assessed_by="automated_checker",
            evidence=evidence,
            findings=findings,
            notes="PCI DSS compliance requires specific cardholder data handling verification",
        )

    async def _check_pci_access_control(
        self, requirement: ComplianceRequirement
    ) -> ComplianceAssessment:
        """Check PCI DSS Access Control"""
        evidence = []
        findings = []
        status = ComplianceStatus.PARTIALLY_COMPLIANT

        if self.session_manager:
            evidence.append("User authentication system implemented")
        else:
            findings.append("No user authentication system")
            status = ComplianceStatus.NON_COMPLIANT

        # PCI DSS requires specific controls that need manual verification
        findings.append(
            "Manual verification required for PCI DSS specific access controls"
        )

        return ComplianceAssessment(
            assessment_id=str(uuid.uuid4()),
            requirement_id=requirement.requirement_id,
            framework=requirement.framework,
            status=status,
            assessed_at=datetime.utcnow(),
            assessed_by="automated_checker",
            evidence=evidence,
            findings=findings,
        )


class ComplianceReportGenerator:
    """Generates compliance reports in various formats"""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Template]:
        """Load report templates"""
        templates = {}

        # HTML template for compliance reports
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ framework|upper }} Compliance Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
                .summary { background-color: #ecf0f1; padding: 20px; margin: 20px 0; border-radius: 5px; }
                .requirement { border: 1px solid #bdc3c7; margin: 10px 0; padding: 15px; border-radius: 3px; }
                .compliant { border-left: 5px solid #27ae60; }
                .non-compliant { border-left: 5px solid #e74c3c; }
                .partially-compliant { border-left: 5px solid #f39c12; }
                .not-assessed { border-left: 5px solid #95a5a6; }
                .evidence { background-color: #d5f4e6; padding: 10px; margin: 10px 0; border-radius: 3px; }
                .findings { background-color: #fadbd8; padding: 10px; margin: 10px 0; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ framework|upper }} Compliance Report</h1>
                <p>Generated on {{ generated_at }} by {{ generated_by }}</p>
                <p>Assessment Period: {{ period_start }} to {{ period_end }}</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <p><strong>Overall Status:</strong> {{ overall_status|upper }}</p>
                <ul>
                    <li>Total Requirements: {{ summary_metrics.total_requirements }}</li>
                    <li>Compliant: {{ summary_metrics.compliant }}</li>
                    <li>Non-Compliant: {{ summary_metrics.non_compliant }}</li>
                    <li>Partially Compliant: {{ summary_metrics.partially_compliant }}</li>
                    <li>Not Assessed: {{ summary_metrics.not_assessed }}</li>
                </ul>
            </div>
            
            <h2>Detailed Assessment Results</h2>
            {% for assessment in assessments %}
            <div class="requirement {{ assessment.status|replace('_', '-') }}">
                <h3>{{ assessment.requirement_id }}</h3>
                <p><strong>Status:</strong> {{ assessment.status|upper }}</p>
                <p><strong>Assessed by:</strong> {{ assessment.assessed_by }}</p>
                <p><strong>Assessment Date:</strong> {{ assessment.assessed_at }}</p>
                
                {% if assessment.evidence %}
                <div class="evidence">
                    <strong>Evidence:</strong>
                    <ul>
                    {% for item in assessment.evidence %}
                        <li>{{ item }}</li>
                    {% endfor %}
                    </ul>
                </div>
                {% endif %}
                
                {% if assessment.findings %}
                <div class="findings">
                    <strong>Findings:</strong>
                    <ul>
                    {% for item in assessment.findings %}
                        <li>{{ item }}</li>
                    {% endfor %}
                    </ul>
                </div>
                {% endif %}
                
                {% if assessment.remediation_plan %}
                <p><strong>Remediation Plan:</strong> {{ assessment.remediation_plan }}</p>
                {% endif %}
                
                {% if assessment.notes %}
                <p><strong>Notes:</strong> {{ assessment.notes }}</p>
                {% endif %}
            </div>
            {% endfor %}
            
            {% if recommendations %}
            <h2>Recommendations</h2>
            <ul>
            {% for rec in recommendations %}
                <li>{{ rec }}</li>
            {% endfor %}
            </ul>
            {% endif %}
        </body>
        </html>
        """

        templates["html"] = Template(html_template)
        return templates

    async def generate_html_report(self, report: ComplianceReport) -> str:
        """Generate HTML compliance report"""
        template = self.templates["html"]
        return template.render(
            framework=report.framework.value,
            generated_at=report.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            generated_by=report.generated_by,
            period_start=report.period_start.strftime("%Y-%m-%d"),
            period_end=report.period_end.strftime("%Y-%m-%d"),
            overall_status=report.overall_status.value,
            summary_metrics=report.summary_metrics,
            assessments=report.assessments,
            recommendations=report.recommendations,
        )

    async def generate_pdf_report(self, report: ComplianceReport) -> bytes:
        """Generate PDF compliance report"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16)

        # Title
        pdf.cell(
            200,
            10,
            txt=f"{report.framework.value.upper()} Compliance Report",
            ln=True,
            align="C",
        )
        pdf.ln(10)

        # Report metadata
        pdf.set_font("Arial", size=12)
        pdf.cell(
            200,
            10,
            txt=f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ln=True,
        )
        pdf.cell(
            200,
            10,
            txt=f"Period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}",
            ln=True,
        )
        pdf.cell(
            200,
            10,
            txt=f"Overall Status: {report.overall_status.value.upper()}",
            ln=True,
        )
        pdf.ln(10)

        # Summary
        pdf.set_font("Arial", "B", size=14)
        pdf.cell(200, 10, txt="Executive Summary", ln=True)
        pdf.set_font("Arial", size=12)

        for key, value in report.summary_metrics.items():
            pdf.cell(200, 8, txt=f"{key.replace('_', ' ').title()}: {value}", ln=True)

        pdf.ln(10)

        # Assessments
        pdf.set_font("Arial", "B", size=14)
        pdf.cell(200, 10, txt="Assessment Results", ln=True)

        for assessment in report.assessments:
            pdf.set_font("Arial", "B", size=12)
            pdf.cell(
                200,
                8,
                txt=f"{assessment.requirement_id} - {assessment.status.value.upper()}",
                ln=True,
            )

            pdf.set_font("Arial", size=10)
            if assessment.findings:
                pdf.cell(200, 6, txt="Findings:", ln=True)
                for finding in assessment.findings[:3]:  # Limit for space
                    pdf.cell(200, 6, txt=f"• {finding[:100]}...", ln=True)

            pdf.ln(5)

        return pdf.output(dest="S").encode("latin1")

    async def generate_csv_report(self, report: ComplianceReport) -> str:
        """Generate CSV compliance report"""
        data = []

        for assessment in report.assessments:
            data.append(
                {
                    "Requirement ID": assessment.requirement_id,
                    "Framework": assessment.framework.value,
                    "Status": assessment.status.value,
                    "Assessed At": assessment.assessed_at.isoformat(),
                    "Assessed By": assessment.assessed_by,
                    "Evidence Count": len(assessment.evidence),
                    "Findings Count": len(assessment.findings),
                    "Has Remediation Plan": bool(assessment.remediation_plan),
                    "Next Assessment Due": (
                        assessment.next_assessment_due.isoformat()
                        if assessment.next_assessment_due
                        else ""
                    ),
                }
            )

        df = pd.DataFrame(data)
        return df.to_csv(index=False)


class ComplianceManager:
    """Main compliance management system"""

    def __init__(
        self,
        redis_client: RedisClient,
        audit_logger: AuditLogger,
        vulnerability_manager: Optional[VulnerabilityManager] = None,
        session_manager: Optional[SessionManager] = None,
        encryption_service: Optional[EncryptionService] = None,
    ):
        self.redis_client = redis_client
        self.audit_logger = audit_logger

        # Components
        self.requirement_registry = ComplianceRequirementRegistry()
        self.automated_checker = AutomatedComplianceChecker(
            redis_client,
            audit_logger,
            vulnerability_manager,
            session_manager,
            encryption_service,
        )
        self.report_generator = ComplianceReportGenerator()

        # Storage
        self.assessments: Dict[str, ComplianceAssessment] = {}
        self.reports: Dict[str, ComplianceReport] = {}

    async def run_compliance_assessment(
        self, framework: ComplianceFramework, assessed_by: str
    ) -> List[ComplianceAssessment]:
        """Run compliance assessment for a framework"""
        requirements = self.requirement_registry.get_requirements(framework)
        assessments = []

        for requirement in requirements:
            assessment = await self.automated_checker.check_requirement(requirement)
            assessments.append(assessment)

            # Store assessment
            self.assessments[assessment.assessment_id] = assessment
            await self._store_assessment(assessment)

        # Log assessment completion
        self.audit_logger.log_event(
            AuditEventType.ADMIN_ACTION,
            f"Compliance assessment completed for {framework.value}",
            user_id=assessed_by,
            details={
                "framework": framework.value,
                "requirements_assessed": len(assessments),
                "compliant": len(
                    [a for a in assessments if a.status == ComplianceStatus.COMPLIANT]
                ),
                "non_compliant": len(
                    [
                        a
                        for a in assessments
                        if a.status == ComplianceStatus.NON_COMPLIANT
                    ]
                ),
            },
        )

        return assessments

    async def generate_compliance_report(
        self,
        framework: ComplianceFramework,
        generated_by: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> ComplianceReport:
        """Generate compliance report"""
        if not period_end:
            period_end = datetime.utcnow()
        if not period_start:
            period_start = period_end - timedelta(days=90)

        # Get recent assessments for the framework
        assessments = [
            assessment
            for assessment in self.assessments.values()
            if (
                assessment.framework == framework
                and period_start <= assessment.assessed_at <= period_end
            )
        ]

        # If no recent assessments, run new assessment
        if not assessments:
            assessments = await self.run_compliance_assessment(framework, generated_by)

        # Calculate summary metrics
        total = len(assessments)
        compliant = len(
            [a for a in assessments if a.status == ComplianceStatus.COMPLIANT]
        )
        non_compliant = len(
            [a for a in assessments if a.status == ComplianceStatus.NON_COMPLIANT]
        )
        partially_compliant = len(
            [a for a in assessments if a.status == ComplianceStatus.PARTIALLY_COMPLIANT]
        )
        not_assessed = len(
            [a for a in assessments if a.status == ComplianceStatus.NOT_ASSESSED]
        )

        # Determine overall status
        if non_compliant == 0 and not_assessed == 0:
            overall_status = ComplianceStatus.COMPLIANT
        elif non_compliant > 0:
            overall_status = ComplianceStatus.NON_COMPLIANT
        else:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT

        # Generate recommendations
        recommendations = self._generate_recommendations(assessments)

        # Create report
        report = ComplianceReport(
            report_id=str(uuid.uuid4()),
            framework=framework,
            generated_at=datetime.utcnow(),
            generated_by=generated_by,
            period_start=period_start,
            period_end=period_end,
            overall_status=overall_status,
            assessments=assessments,
            summary_metrics={
                "total_requirements": total,
                "compliant": compliant,
                "non_compliant": non_compliant,
                "partially_compliant": partially_compliant,
                "not_assessed": not_assessed,
                "compliance_percentage": (
                    round((compliant / total) * 100, 1) if total > 0 else 0
                ),
            },
            recommendations=recommendations,
        )

        # Store report
        self.reports[report.report_id] = report
        await self._store_report(report)

        return report

    def _generate_recommendations(
        self, assessments: List[ComplianceAssessment]
    ) -> List[str]:
        """Generate recommendations based on assessment results"""
        recommendations = []

        # Count non-compliant by category
        non_compliant_count = len(
            [a for a in assessments if a.status == ComplianceStatus.NON_COMPLIANT]
        )

        if non_compliant_count > 0:
            recommendations.append(
                f"Address {non_compliant_count} non-compliant requirements immediately"
            )

        # Check for encryption-related issues
        encryption_issues = [
            a for a in assessments if "encryption" in " ".join(a.findings).lower()
        ]
        if encryption_issues:
            recommendations.append("Review and strengthen encryption implementation")

        # Check for access control issues
        access_issues = [
            a for a in assessments if "access" in " ".join(a.findings).lower()
        ]
        if access_issues:
            recommendations.append("Enhance access control mechanisms")

        # Check for monitoring issues
        monitoring_issues = [
            a for a in assessments if "monitoring" in " ".join(a.findings).lower()
        ]
        if monitoring_issues:
            recommendations.append("Improve security monitoring and logging")

        return recommendations

    async def get_compliance_dashboard_data(self) -> Dict[str, Any]:
        """Get compliance dashboard data"""
        frameworks_status = {}

        for framework in ComplianceFramework:
            if framework == ComplianceFramework.CUSTOM:
                continue

            # Get latest assessments for each framework
            framework_assessments = [
                a for a in self.assessments.values() if a.framework == framework
            ]

            if framework_assessments:
                # Sort by assessment date and take most recent
                framework_assessments.sort(key=lambda x: x.assessed_at, reverse=True)
                recent_assessments = framework_assessments[:10]  # Last 10 assessments

                total = len(recent_assessments)
                compliant = len(
                    [
                        a
                        for a in recent_assessments
                        if a.status == ComplianceStatus.COMPLIANT
                    ]
                )

                frameworks_status[framework.value] = {
                    "total_requirements": total,
                    "compliant": compliant,
                    "compliance_percentage": (
                        round((compliant / total) * 100, 1) if total > 0 else 0
                    ),
                    "last_assessed": framework_assessments[0].assessed_at.isoformat(),
                }
            else:
                frameworks_status[framework.value] = {
                    "total_requirements": 0,
                    "compliant": 0,
                    "compliance_percentage": 0,
                    "last_assessed": None,
                }

        return {
            "frameworks": frameworks_status,
            "total_reports": len(self.reports),
            "total_assessments": len(self.assessments),
        }

    async def _store_assessment(self, assessment: ComplianceAssessment):
        """Store assessment in Redis"""
        try:
            await self.redis_client.client.set(
                f"compliance_assessment:{assessment.assessment_id}",
                json.dumps(assessment.to_dict()),
                ex=86400 * 365,  # Keep for 1 year
            )
        except Exception as e:
            logger.error(f"Error storing assessment: {e}")

    async def _store_report(self, report: ComplianceReport):
        """Store report in Redis"""
        try:
            await self.redis_client.client.set(
                f"compliance_report:{report.report_id}",
                json.dumps(report.to_dict()),
                ex=86400 * 365,  # Keep for 1 year
            )
        except Exception as e:
            logger.error(f"Error storing report: {e}")


# Factory function
async def setup_compliance_manager(
    redis_client: RedisClient,
    audit_logger: AuditLogger,
    vulnerability_manager: Optional[VulnerabilityManager] = None,
    session_manager: Optional[SessionManager] = None,
    encryption_service: Optional[EncryptionService] = None,
) -> ComplianceManager:
    """Setup compliance management system"""
    manager = ComplianceManager(
        redis_client,
        audit_logger,
        vulnerability_manager,
        session_manager,
        encryption_service,
    )

    logger.info("Compliance management system initialized")
    return manager


# FastAPI routes for compliance management
def create_compliance_routes(app: FastAPI, compliance_manager: ComplianceManager):
    """Add compliance management routes to FastAPI app"""

    @app.post("/compliance/assess/{framework}")
    async def run_assessment(framework: str, assessed_by: str = "system"):
        """Run compliance assessment for framework"""
        try:
            framework_enum = ComplianceFramework(framework)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid framework")

        assessments = await compliance_manager.run_compliance_assessment(
            framework_enum, assessed_by
        )

        return {
            "framework": framework,
            "assessments_completed": len(assessments),
            "compliant": len(
                [a for a in assessments if a.status == ComplianceStatus.COMPLIANT]
            ),
            "non_compliant": len(
                [a for a in assessments if a.status == ComplianceStatus.NON_COMPLIANT]
            ),
        }

    @app.post("/compliance/report/{framework}")
    async def generate_report(
        framework: str, format: str = "html", generated_by: str = "system"
    ):
        """Generate compliance report"""
        try:
            framework_enum = ComplianceFramework(framework)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid framework")

        report = await compliance_manager.generate_compliance_report(
            framework_enum, generated_by
        )

        if format == "html":
            content = await compliance_manager.report_generator.generate_html_report(
                report
            )
            return {"report_id": report.report_id, "format": "html", "content": content}
        elif format == "csv":
            content = await compliance_manager.report_generator.generate_csv_report(
                report
            )
            return {"report_id": report.report_id, "format": "csv", "content": content}
        else:
            return {"report_id": report.report_id, "summary": report.summary_metrics}

    @app.get("/compliance/dashboard")
    async def get_compliance_dashboard():
        """Get compliance dashboard data"""
        return await compliance_manager.get_compliance_dashboard_data()

    @app.get("/compliance/requirements/{framework}")
    async def get_requirements(framework: str):
        """Get requirements for framework"""
        try:
            framework_enum = ComplianceFramework(framework)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid framework")

        requirements = compliance_manager.requirement_registry.get_requirements(
            framework_enum
        )
        return {
            "framework": framework,
            "requirements": [req.to_dict() for req in requirements],
        }
