# 🧠 AGENTS.md  
**Mission-Critical Agent Development Standards for MCP**

---

## 🔐 Purpose  
This document defines the **non-negotiable rules** and **best practices** for building and maintaining all agent modules within the MCP (Multimodal Content Processor) platform.

Agents are core autonomous units responsible for executing specialized tasks in secure, production-grade pipelines. This guide ensures all agents meet the highest engineering, security, and deployment standards.

---

## MCP Codex Agent Capabilities and Multi-User Enterprise Architecture

### Core Agent Registry

| Agent | Capability | Input Format | Output Format | Access Level | Data Isolation |
|-------|------------|--------------|---------------|--------------|----------------|
| Model Router | Routes requests to the optimal Claude model | JSON over HTTP | JSON | internal (port 8001) | stateless |
| Plan Management | Stores and versions project plans | JSON over HTTP | JSON | internal (port 8002) | volume `plan_storage` |
| Git Worktree Manager | Manages Git repositories and worktrees | JSON over HTTP | JSON | internal (port 8003) | volume `git_repositories` |
| Workflow Orchestrator | Coordinates multi-step workflows | JSON over HTTP | JSON | internal (port 8004) | database per workflow |
| Verification Feedback | Performs code analysis and quality checks | JSON over HTTP | JSON | internal (port 8005) | ephemeral workspace |

---

## ✅ CRITICAL COMPLIANCE CHECKLIST  

Every agent must fully comply with **all** of the following before merge or deployment:

| Requirement                          | Description                                                                                 | Status Check |
|--------------------------------------|---------------------------------------------------------------------------------------------|--------------|
| **✅ NO PLACEHOLDERS**               | Verify all placeholders and TODOs are replaced with production-ready, enterprise-grade code. No stubs, no empty functions. | ✔ Required   |
| **✅ NO `TODO:` COMMENTS**           | If a feature is listed, it must be implemented in full. No scaffolding or intent-only code.| ✔ Required   |
| **✅ NO PSEUDO-CODE**                | Only executable Python (or approved language) code permitted.                              | ✔ Required   |
| **✅ NO MISSING IMPORTS**            | All external dependencies must be declared and imported cleanly.                           | ✔ Required   |
| **✅ PASSES LINTING**                | Code must pass all linters (e.g., `ruff`, `black`, `mypy`) with zero errors or warnings.   | ✔ Required   |
| **✅ PASSES UNIT + INTEGRATION TESTS**| Each agent must include `tests/` folder with functional test coverage ≥ 80%.              | ✔ Required   |
| **✅ DOCUMENTED**                    | Each agent must include docstrings, `README.md`, and inline comments for maintainability.  | ✔ Required   |

---

## 📦 Standard Agent Folder Structure

```bash
agents/
└── {AgentName}/
    ├── __init__.py
    ├── main.py             # Entry point
    ├── config.py           # Static config & constants
    ├── schema.py           # Pydantic data models
    ├── utils.py            # Optional shared helpers
    ├── README.md           # Agent overview and usage
    └── tests/
        └── test_main.py    # Full test coverage
```

---

## 🧱 Required Components per Agent

| File         | Purpose                                                                 |
|--------------|-------------------------------------------------------------------------|
| `main.py`    | The primary logic controller. Must expose a callable `run(input)` function. |
| `config.py`  | Contains non-secret constants, URLs, task parameters, etc.               |
| `schema.py`  | Defines `InputSchema`, `OutputSchema`, and intermediate data structures. |
| `README.md`  | Describes what the agent does, how it works, and how to test it.         |
| `tests/`     | All tests must run via `pytest` or `unittest` and use real mock data.    |

---

## 🔄 Agent Lifecycle Standards

Each agent must:

1. **Initialize Securely**  
   - No hardcoded secrets. Use environment variables or secret manager integrations.

2. **Validate Input/Output**  
   - Use `pydantic` for data contracts.
   - Raise clear errors on malformed inputs.

3. **Handle Failures Gracefully**  
   - Log structured error output (`loguru` or `structlog`).
   - Return traceable error codes for upstream pipelines.

4. **Track Performance**  
   - Emit telemetry (`stdout` or OpenTelemetry trace if configured).
   - Record duration of major steps.

5. **Log Activity**  
   - Store logs in rotating files or a centralized store.
   - Use unique request/session IDs.

---

## ⚙️ Example Agent Blueprint

```python
# main.py
from .schema import InputSchema, OutputSchema
from .utils import process_task

def run(input_data: dict) -> dict:
    parsed = InputSchema(**input_data)
    result = process_task(parsed)
    return OutputSchema.from_result(result).dict()
```

---

## 🧪 Test Example

```python
# tests/test_main.py
from agents.ExampleAgent.main import run

def test_run_returns_expected_output():
    input_data = {"prompt": "Hello world"}
    result = run(input_data)
    assert "response" in result
```

---

## 🔐 Secure Agent Requirements

| Security Principle      | Enforcement Notes                                               |
|-------------------------|------------------------------------------------------------------|
| No plaintext secrets    | Use `.env`, HashiCorp Vault, or secrets manager                 |
| Zero external calls w/o validation | All HTTP requests must validate schema + handle 4xx/5xx codes        |
| Sanitize input/output   | All user-generated inputs must be escaped and validated         |
| Enforced RBAC/Scopes    | If agent accesses protected resources, it must verify permissions |

---

## 📜 Naming Conventions

- `AgentName` must use `PascalCase`
- All functions must use `snake_case`
- All constants in `config.py` must be `UPPER_SNAKE_CASE`

---

### Compliance and Governance Framework

### Privacy-First Agent Architecture

#### Data Minimization Principles
- **Purpose Limitation**: Agents only access data necessary for their specific function
- **Storage Limitation**: Data automatically purged based on retention policies
- **Accuracy**: Regular data validation and correction workflows
- **Transparency**: Clear data processing notifications to users
- **User Control**: Granular consent management and data portability

#### Agent Privacy Controls
```yaml
agent_privacy_framework:
  data_access_control:
    - tenant_scoped_queries
    - purpose_based_filtering
    - minimal_data_principle
    - automatic_data_masking
    - consent_verification
    
  data_processing_limits:
    - retention_period_enforcement
    - geographical_restrictions
    - usage_purpose_validation
    - third_party_sharing_controls
    - anonymization_requirements
    
  audit_and_transparency:
    - processing_activity_logs
    - data_lineage_tracking
    - consent_trail_maintenance
    - user_notification_system
    - data_subject_request_handling
```

#### Multi-Jurisdiction Compliance
```yaml
compliance_requirements:
  gdpr_compliance:
    - right_to_be_forgotten
    - data_portability
    - consent_management
    - privacy_by_design
    - data_protection_impact_assessments
    
  ccpa_compliance:
    - consumer_privacy_rights
    - data_sale_restrictions
    - opt_out_mechanisms
    - third_party_disclosure_tracking
    - consumer_request_processing
    
  hipaa_compliance:
    - healthcare_data_protection
    - minimum_necessary_standard
    - business_associate_agreements
    - audit_log_requirements
    - breach_notification_procedures
    
  sox_compliance:
    - financial_data_controls
    - audit_trail_integrity
    - segregation_of_duties
    - change_management_controls
    - executive_certification_requirements
```

#### Data Governance Automation
```yaml
governance_automation:
  data_discovery:
    - automatic_pii_detection
    - sensitive_data_classification
    - data_flow_mapping
    - compliance_gap_analysis
    - risk_assessment_automation
    
  policy_enforcement:
    - automated_access_controls
    - data_retention_automation
    - consent_expiry_monitoring
    - compliance_violation_detection
    - remediation_workflow_triggers
    
  reporting_and_monitoring:
    - compliance_dashboard
    - audit_report_generation
    - risk_metric_tracking
    - violation_trend_analysis
    - regulatory_change_monitoring
```

---

## 🚨 Lint & QA Hooks

Agents are automatically checked via CI/CD. Local devs must pass:

```bash
# Format & lint
ruff check .
black .
mypy .

# Run tests
pytest tests/
```

Failing any of the above will block merge.

---

## 🧠 Examples of Valid Agents

- ✅ `CuratorAgent`: Gathers and filters top AI compliance news.
- ✅ `RiskScoreAgent`: Calculates AI Risk Pulse scores from Typeform submissions.
- ✅ `AuditAgent`: Audits Notion workspace for compliance and status drift.

---

## 🔄 Contribution Process

1. Fork → Feature Branch (`agent/{agent-name}`)
2. Add complete, working files per structure above
3. Open PR with linked issue + test results
4. Peer-reviewed and merged on green CI

---

### Future Roadmap: Enterprise-Grade Features

#### Advanced Security Features
- **Zero Trust Architecture**: Continuous verification of all access requests
- **Advanced Threat Detection**: AI-powered anomaly detection for data access patterns
- **Quantum-Safe Encryption**: Preparation for post-quantum cryptography
- **Blockchain Audit Trails**: Immutable audit logging for high-compliance environments

#### Global Scaling Capabilities
- **Multi-Region Data Residency**: Automatic data localization based on user location
- **Edge Computing Integration**: Reduce latency with edge-based agent processing
- **Advanced Caching**: Intelligent caching with privacy preservation
- **Global Load Balancing**: Seamless scaling across multiple geographic regions

#### AI-Powered Governance
- **Intelligent Data Classification**: AI-powered automatic data sensitivity detection
- **Predictive Compliance**: AI models to predict and prevent compliance violations
- **Automated Risk Assessment**: Continuous risk scoring and mitigation recommendations
- **Smart Data Retention**: AI-optimized data retention policies

---

## 📞 Questions?

Contact `@mikeholownych` or open an issue with `[Agent Question]` in the title.
