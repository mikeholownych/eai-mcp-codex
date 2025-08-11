# Payment System File Map

This document maps the location of all payment system artifacts in the codebase.

## Backend Implementation

### Core Payment Service
- **Service Entry Point**: `src/payments/app.py` - FastAPI application with payment routes
- **Main Routes**: `src/payments/routes.py` - Payment intent, refund, webhook endpoints
- **Service Layer**: `src/payments/services.py` - Business logic for payment operations
- **Models**: `src/payments/models.py` - Pydantic models for requests/responses
- **Database Models**: `src/payments/db_models.py` - SQLAlchemy ORM models

### Payment Gateways
- **Stripe Gateway**: `src/payments/gateways/stripe_gateway.py` - Stripe API integration
- **Mock Gateway**: `src/payments/gateways/mock_gateway.py` - Development/testing gateway
- **Base Gateway**: `src/payments/gateways/base.py` - Abstract gateway interface
- **Gateway Factory**: `src/payments/gateways/factory.py` - Provider selection logic

### Webhook Processing
- **Webhook Handler**: `src/payments/webhooks/handler.py` - Event processing logic
- **Event Processor**: `src/payments/webhooks/processor.py` - Async event processing
- **Signature Verifier**: `src/payments/webhooks/verifier.py` - Stripe signature validation

### Database
- **Migrations**: `database/migrations/versions/` - Alembic migration files
- **Initial Schema**: `database/migrations/versions/0002_payments_schema.py`
- **Seed Data**: `database/seeds/payment_test_data.sql`

### Configuration
- **Environment Schema**: `src/payments/config.py` - Pydantic settings validation
- **Feature Flags**: `src/payments/features.py` - Payment method availability flags

## Frontend Implementation

### React Components
- **Payment Form**: `frontend/src/components/payments/PaymentForm.tsx` - Main payment form
- **Stripe Elements**: `frontend/src/components/payments/StripeElements.tsx` - Card input component
- **Payment Request Button**: `frontend/src/components/payments/PaymentRequestButton.tsx` - Apple/Google Pay
- **3DS Modal**: `frontend/src/components/payments/ThreeDSModal.tsx` - 3DS challenge handling
- **Receipt View**: `frontend/src/components/payments/ReceiptView.tsx` - Payment confirmation

### Payment Pages
- **Checkout Page**: `frontend/src/pages/Checkout.tsx` - Main checkout flow
- **Payment Status**: `frontend/src/pages/PaymentStatus.tsx` - Payment result display
- **Payment History**: `frontend/src/pages/PaymentHistory.tsx` - User payment history

### Hooks & Utilities
- **Payment Hook**: `frontend/src/hooks/usePayment.ts` - Payment state management
- **Stripe Hook**: `frontend/src/hooks/useStripe.ts` - Stripe.js integration
- **Currency Utils**: `frontend/src/utils/currency.ts` - Currency formatting helpers

### Types
- **Payment Types**: `frontend/src/types/payments.ts` - TypeScript interfaces

## CLI & Operations

### CLI Commands
- **Payment CLI**: `tools/payment-cli.py` - Command-line payment operations
- **Seed Data**: `tools/seed-payment-data.py` - Test data generation
- **Reconciliation**: `tools/reconcile-payments.py` - Payment reconciliation script

### Operations Scripts
- **Stripe CLI Setup**: `tools/stripe-setup.sh` - Stripe CLI configuration
- **Webhook Forwarding**: `tools/stripe-webhook-forward.sh` - Local webhook testing
- **Payment Monitoring**: `tools/monitor-payments.sh` - Payment health monitoring

## Testing

### Unit Tests
- **Gateway Tests**: `tests/unit/test_payment_gateways.py` - Gateway unit tests
- **Service Tests**: `tests/unit/test_payment_services.py` - Service layer tests
- **Webhook Tests**: `tests/unit/test_webhooks.py` - Webhook processing tests

### Integration Tests
- **Payment Flow Tests**: `tests/integration/test_payment_flows.py` - End-to-end payment tests
- **Stripe Integration**: `tests/integration/test_stripe_integration.py` - Stripe API tests
- **Mock Gateway**: `tests/integration/test_mock_gateway.py` - Mock gateway tests

### E2E Tests
- **Playwright Tests**: `tests/e2e/payment_flows.spec.ts` - Browser-based payment tests
- **Test Configuration**: `tests/e2e/payment.config.ts` - E2E test configuration

## CI/CD & Infrastructure

### GitHub Actions
- **Payment CI**: `.github/workflows/payments-ci.yml` - Payment system CI pipeline
- **Local CI Script**: `ci_local.sh` - Local CI execution script

### Docker
- **Payment Service**: `docker/payment-service.Dockerfile` - Payment service container
- **Docker Compose**: `docker-compose.payments.yml` - Payment service orchestration

### Environment Files
- **Example Environment**: `.env.example` - Environment variable examples
- **Environment Schema**: `env.schema.py` - Environment validation schema

## Monitoring & Observability

### Dashboards
- **SQL Queries**: `launch/dashboards/sql/` - Payment metrics SQL queries
- **Grafana Dashboards**: `launch/dashboards/grafana/` - Grafana dashboard JSON
- **Metabase**: `launch/dashboards/metabase/` - Metabase dashboard exports

### n8n Automations
- **Health Check**: `automations/n8n/payments_healthcheck.json` - Payment health monitoring
- **Failure Alerts**: `automations/n8n/payments_failures_alert.json` - Failure threshold alerts
- **Reconciliation**: `automations/n8n/payout_reconcile_digest.json` - Payment reconciliation

### Runbooks
- **On-Call Runbook**: `docs/ops/payments_oncall.md` - Payment incident response

## Documentation

### Architecture
- **Payment Architecture**: `docs/payments/PAYMENT_ARCHITECTURE.md` - System design document
- **API Documentation**: `docs/payments/api.md` - Payment API reference
- **Integration Guide**: `docs/payments/integration.md` - Frontend integration guide

### Compliance
- **PCI Compliance**: `docs/payments/pci_compliance.md` - PCI DSS compliance guide
- **SCA Guide**: `docs/payments/sca_guide.md` - Strong Customer Authentication guide
- **Regional Compliance**: `docs/payments/regional_compliance.md` - Country-specific requirements

## Dependencies

### Python Dependencies
- **Stripe**: `stripe>=7.0.0` - Stripe Python library
- **Redis**: `redis>=4.0.0` - Redis client for webhook queue
- **SQLAlchemy**: `sqlalchemy>=1.4.0` - Database ORM
- **Alembic**: `alembic>=1.7.0` - Database migrations

### Frontend Dependencies
- **Stripe.js**: `@stripe/stripe-js` - Stripe JavaScript library
- **React Stripe**: `@stripe/react-stripe-js` - React Stripe components
- **Payment Request**: `@stripe/stripe-js/pure` - Payment Request API support

### Development Dependencies
- **Stripe CLI**: `stripe` - Stripe command-line tool
- **Stripe Mock**: `stripe-mock` - Stripe API mocking server
- **Test Cards**: Various test card numbers for different scenarios
