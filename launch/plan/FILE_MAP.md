# File Map: Ethical AI Insider — MCP Codex Launch Assets

This document maps the location of all launch assets created for the Ethical AI Insider — MCP Codex growth architecture.

## Phase 1: PLAN (Strategy + ICP + Offer)

### Core Strategy Documents
- `launch/plan/AUDIT_AND_PLAN.md` - Complete growth architecture audit and plan
- `launch/plan/OFFER.md` - PLG value path + Sales-Assist handoff strategy

### Brand & Positioning
- `launch/brand/POSITIONING.md` - Product positioning and differentiation
- `launch/brand/MESSAGING_MATRIX.md` - ICP × funnel stage messaging matrix

## Phase 2: DESIGN (Brand + Web + Templates)

### Brand System
- `launch/brand/logo.svg` - Product logo (SVG format)
- `launch/brand/palette.json` - Color palette with WCAG AA/AAA contrast scores
- `launch/brand/VOICE_TONE.md` - Brand voice and tone guidelines

### Website Pages
- `website/landing.md` - Landing page copy and section structure
- `website/pricing.md` - Pricing page copy and section structure

### Email & Lifecycle Templates
- `launch/templates/email/onboarding.md` - Onboarding email template
- `launch/templates/email/activation.md` - Activation nudge email template
- `launch/templates/email/revival.md` - Revival email template
- `launch/templates/email/beta_invite.md` - Beta invitation email template

### Sales-Assist Kit
- `launch/sales/discovery_script.md` - Discovery call script
- `launch/sales/demo_script.md` - Product demo script
- `launch/sales/battlecards.md` - Competitive battlecards
- `launch/sales/objection_handling.md` - Objection handling guide
- `launch/sales/roi_calculator.xlsx` - ROI calculator with prefilled examples

## Phase 3: IMPLEMENT (Telemetry + PLG + Automations)

### Telemetry & Instrumentation
- `launch/telemetry/events.schema.json` - Event schema with PII flags
- `launch/telemetry/METRICS.md` - Metrics definitions and data flow diagrams
- `launch/telemetry/sql/` - SQL queries for key metrics
  - `launch/telemetry/sql/ttf_signup_to_first_success.sql`
  - `launch/telemetry/sql/activation_rate_7d.sql`
  - `launch/telemetry/sql/pql_rate.sql`
  - `launch/telemetry/sql/mql_to_sql.sql`
  - `launch/telemetry/sql/nrr_structure.sql`

### Code Instrumentation
- `app/instrumentation/python/` - Python telemetry code
- `app/instrumentation/node/` - Node.js telemetry code

### n8n Automations
- `automations/n8n/lead_capture_enrich_route.json` - Lead capture workflow
- `automations/n8n/pql_score_daily.json` - PQL scoring workflow
- `automations/n8n/healthcheck_n8n.json` - Health check workflow
- `automations/n8n/weekly_pipeline_digest.json` - Weekly digest workflow
- `automations/n8n/content_revision_alerts.json` - Content alerts workflow

## Phase 4: DASHBOARDS & SALES-ASSIST KIT

### Analytics Dashboards
- `dashboards/metabase/` - Metabase dashboard exports (JSON)
  - `dashboards/metabase/acquisition.json`
  - `dashboards/metabase/activation.json`
  - `dashboards/metabase/pql_funnel.json`
  - `dashboards/metabase/retention_expansion.json`
- `dashboards/grafana/` - Grafana dashboard exports (JSON)
  - `dashboards/grafana/growth_core.json`
  - `dashboards/grafana/sales_assist.json`

### SQL Queries
- `dashboards/sql/` - SQL queries for dashboard metrics
  - `dashboards/sql/acquisition_metrics.sql`
  - `dashboards/sql/activation_funnel.sql`
  - `dashboards/sql/pql_scoring.sql`
  - `dashboards/sql/retention_cohorts.sql`

## Phase 5: 90-DAY EXPERIMENTS + RUNBOOK

### Growth Planning
- `launch/plan/EXPERIMENTS.md` - 90-day experiment plan (12-16 experiments)
- `launch/plan/ROADMAP_90D.md` - Week-by-week implementation roadmap

### CI/CD & Testing
- `ci_local.sh` - Local CI script mirroring production pipeline
- `.github/workflows/ci.yml` - GitHub Actions workflow with growth tests

## Documentation & Evidence

### Implementation Evidence
- `docs/EVIDENCE.md` - Screenshots and links to working systems
- `docs/RELEASE_NOTES.md` - Release notes for launch
- `docs/CHANGELOG.md` - Change log tracking

### Configuration Files
- `.env.example` - Environment variable template
- `docker-compose.yml` - Local development environment
- `helm/mcp-services/` - Kubernetes deployment configurations

## File Organization Principles

### Directory Structure
- **`launch/`** - All launch-related assets organized by phase
- **`website/`** - Web page content and copy
- **`automations/`** - n8n workflow exports
- **`dashboards/`** - Analytics dashboard configurations
- **`app/`** - Application code and instrumentation
- **`docs/`** - Documentation and evidence

### Naming Conventions
- **Directories**: lowercase with hyphens (`launch/plan/`)
- **Files**: descriptive names with appropriate extensions
- **Assets**: organized by type and phase
- **Templates**: clear purpose indicators in filenames

### Version Control
- All assets committed to repository
- Conventional commit messages for each phase
- Atomic commits for easy rollback
- No secrets or credentials in repository

## Asset Status Tracking

### Completed (Phase 1)
- ✅ `launch/plan/AUDIT_AND_PLAN.md`
- ✅ `launch/plan/OFFER.md`
- ✅ `launch/brand/POSITIONING.md`
- ✅ `launch/brand/MESSAGING_MATRIX.md`

### In Progress
- 🔄 `launch/plan/FILE_MAP.md` (this document)

### Pending
- ⏳ Brand system (logo.svg, palette.json, VOICE_TONE.md)
- ⏳ Website pages (landing.md, pricing.md)
- ⏳ Email templates (onboarding, activation, revival, beta_invite)
- ⏳ Sales kit (scripts, battlecards, objections, ROI calculator)
- ⏳ Telemetry (events schema, instrumentation, metrics)
- ⏳ n8n automations (5 workflows)
- ⏳ Dashboards (Metabase/Grafana exports)
- ⏳ 90-day experiments plan
- ⏳ CI/CD configuration

## Next Steps

1. **Complete Phase 1**: Review and approve PLAN deliverables
2. **Begin Phase 2**: Create brand system and web content
3. **Continue Phase 3**: Implement telemetry and automations
4. **Execute Phase 4**: Build dashboards and sales kit
5. **Finalize Phase 5**: Plan experiments and configure CI/CD

---

*This file map will be updated as assets are created and committed to the repository.*
