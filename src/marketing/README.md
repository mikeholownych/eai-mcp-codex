# Marketing Service

A comprehensive marketing automation and lead management service for the MCP platform. This service provides sales funnel management, lead tracking, email campaigns, A/B testing, analytics, and CRM integration capabilities.

## Features

### 🎯 Sales Funnel Management
- **Multi-stage funnels**: Create and manage complex sales funnels with custom stages
- **Lead progression tracking**: Monitor leads as they move through funnel stages
- **Conversion optimization**: Analyze and optimize conversion rates at each stage
- **Performance metrics**: Track funnel performance with detailed analytics

### 📧 Email Marketing
- **Template management**: Create and manage HTML/Text email templates
- **Campaign creation**: Build targeted email campaigns with segmentation
- **Automated sequences**: Set up drip campaigns and nurture sequences
- **Delivery tracking**: Monitor email delivery, opens, and clicks

### 🧪 A/B Testing
- **Multi-variant testing**: Test different versions of campaigns, landing pages, and content
- **Statistical significance**: Built-in statistical analysis for reliable results
- **Traffic splitting**: Intelligent traffic distribution between variants
- **Winner selection**: Automatic winner selection based on performance metrics

### 📊 Analytics & Reporting
- **Real-time tracking**: Monitor marketing performance in real-time
- **Lead journey analysis**: Track individual lead progression and behavior
- **Campaign performance**: Comprehensive metrics for email campaigns
- **Conversion attribution**: Understand which marketing activities drive conversions

### 🔄 CRM Integration
- **Multi-provider support**: Integrate with Salesforce, HubSpot, and other CRM systems
- **Bidirectional sync**: Keep lead data synchronized between systems
- **Custom field mapping**: Flexible field mapping for different CRM systems
- **Real-time updates**: Automatic synchronization of lead changes

### 🤖 Marketing Automation
- **Trigger-based rules**: Automate marketing actions based on lead behavior
- **Workflow automation**: Create complex marketing workflows
- **Lead scoring**: Automatic lead qualification and scoring
- **Smart segmentation**: Dynamic audience segmentation based on behavior

## Architecture

The marketing service follows a microservices architecture with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App  │    │   Redis Cache   │    │  PostgreSQL DB  │
│                 │    │                 │    │                 │
│  - Routes      │◄──►│  - Sessions     │◄──►│  - Leads        │
│  - Middleware  │    │  - Templates    │    │  - Campaigns    │
│  - Validation  │    │  - Analytics    │    │  - Funnels      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Business      │    │   External      │    │   Monitoring    │
│  Logic Layer   │    │   Integrations  │    │   & Logging     │
│                 │    │                 │    │                 │
│  - Lead Mgmt   │    │  - Email SMTP   │    │  - Prometheus   │
│  - Funnel Mgmt │    │  - CRM APIs     │    │  - Jaeger       │
│  - Analytics   │    │  - Webhooks     │    │  - Structured   │
│  - Automation  │    │  - Third-party  │    │    Logging      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## API Endpoints

### Sales Funnel Management
- `POST /api/marketing/funnels` - Create a new sales funnel
- `GET /api/marketing/funnels` - List all sales funnels
- `GET /api/marketing/funnels/{funnel_id}` - Get specific funnel details
- `POST /api/marketing/funnels/{funnel_id}/leads` - Add lead to funnel
- `GET /api/marketing/funnels/{funnel_id}/performance` - Get funnel performance

### Lead Management
- `POST /api/marketing/leads` - Create a new lead
- `GET /api/marketing/leads` - List leads with filtering
- `GET /api/marketing/leads/{lead_id}` - Get specific lead details
- `PUT /api/marketing/leads/{lead_id}` - Update lead information
- `POST /api/marketing/leads/{lead_id}/qualify` - Qualify a lead

### Email Marketing
- `POST /api/marketing/email/templates` - Create email template
- `POST /api/marketing/email/campaigns` - Create email campaign
- `POST /api/marketing/email/campaigns/{campaign_id}/send` - Send campaign

### A/B Testing
- `POST /api/marketing/ab-testing/experiments` - Create experiment
- `POST /api/marketing/ab-testing/experiments/{experiment_id}/start` - Start experiment
- `GET /api/marketing/ab-testing/experiments/{experiment_id}/results` - Get results

### Analytics
- `GET /api/marketing/analytics/dashboard` - Get marketing dashboard data
- `GET /api/marketing/analytics/leads/{lead_id}/journey` - Get lead journey

### CRM Integration
- `POST /api/marketing/crm/sync/{provider}` - Sync data with CRM

### Automation
- `POST /api/marketing/automation/rules` - Create automation rule
- `POST /api/marketing/automation/sequences` - Create email sequence

## Configuration

The service can be configured through environment variables and configuration files:

### Environment Variables
```bash
# Service Configuration
SERVICE_PORT=8008
SERVICE_HOST=0.0.0.0
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost/mcp

# Redis
REDIS_URL=redis://localhost:6379

# Consul
CONSUL_URL=http://localhost:8500

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Configuration File
```yaml
# config/marketing.yml
email:
  smtp:
    host: smtp.gmail.com
    port: 587
    username: ${SMTP_USERNAME}
    password: ${SMTP_PASSWORD}
    use_tls: true
  
  templates:
    default_sender: "noreply@mcp.com"
    default_sender_name: "MCP Marketing"

crm:
  providers:
    salesforce:
      api_version: "58.0"
      auth_url: "https://login.salesforce.com/services/oauth2/token"
    hubspot:
      api_version: "v3"
      base_url: "https://api.hubapi.com"

analytics:
  tracking:
    enabled: true
    events:
      - lead_created
      - email_opened
      - email_clicked
      - funnel_progress
      - conversion

automation:
  rules:
    enabled: true
    max_rules: 100
  sequences:
    enabled: true
    max_sequences: 50
    max_emails_per_sequence: 10
```

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Consul (optional, for service discovery)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd eai-mcp-codex
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/mcp"
   export REDIS_URL="redis://localhost:6379"
   export SERVICE_PORT=8008
   ```

4. **Run the service**
   ```bash
   python -m src.marketing.app
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -f docker/marketing-service.Dockerfile -t mcp-marketing-service .
   ```

2. **Run the container**
   ```bash
   docker run -p 8008:8008 \
     -e DATABASE_URL="postgresql://user:pass@host:5432/mcp" \
     -e REDIS_URL="redis://host:6379" \
     mcp-marketing-service
   ```

### Kubernetes Deployment

1. **Apply the deployment**
   ```bash
   kubectl apply -f kubernetes/deployments/marketing-service.yaml
   ```

2. **Check deployment status**
   ```bash
   kubectl get pods -n mcp -l app=marketing-service
   ```

## Usage Examples

### Creating a Sales Funnel

```python
import requests

# Create a sales funnel
funnel_data = {
    "name": "E-commerce Conversion Funnel",
    "description": "Funnel for converting website visitors to customers",
    "stages": [
        {"name": "Awareness", "order": 1, "criteria": {}},
        {"name": "Interest", "order": 2, "criteria": {"page_views": 3}},
        {"name": "Decision", "order": 3, "criteria": {"cart_added": True}},
        {"name": "Purchase", "order": 4, "criteria": {"order_completed": True}}
    ],
    "target_audience": {"source": "organic_search"},
    "conversion_goals": {"target_conversion_rate": 0.03}
}

response = requests.post(
    "http://localhost:8008/api/marketing/funnels",
    json=funnel_data,
    headers={"Authorization": "Bearer your-token"}
)

funnel = response.json()
print(f"Created funnel: {funnel['id']}")
```

### Managing Leads

```python
# Create a new lead
lead_data = {
    "email": "john.doe@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "company": "Tech Corp",
    "job_title": "CTO",
    "lead_source": "website",
    "priority": "high"
}

response = requests.post(
    "http://localhost:8008/api/marketing/leads",
    json=lead_data,
    headers={"Authorization": "Bearer your-token"}
)

lead = response.json()
print(f"Created lead: {lead['id']}")

# Add lead to funnel
funnel_response = requests.post(
    f"http://localhost:8008/api/marketing/funnels/{funnel['id']}/leads",
    json=lead_data,
    headers={"Authorization": "Bearer your-token"}
)
```

### Email Campaigns

```python
# Create email template
template_data = {
    "name": "Welcome Template",
    "subject": "Welcome to our platform!",
    "html_content": "<h1>Welcome {{first_name}}!</h1><p>We're excited to have you on board.</p>",
    "variables": ["first_name"],
    "category": "onboarding"
}

template_response = requests.post(
    "http://localhost:8008/api/marketing/email/templates",
    json=template_data,
    headers={"Authorization": "Bearer your-token"}
)

template = template_response.json()

# Create campaign
campaign_data = {
    "name": "Welcome Campaign",
    "template_id": template["template_id"],
    "subject_line": "Welcome to our platform!",
    "sender_name": "Marketing Team",
    "sender_email": "marketing@company.com",
    "target_audience": {"user_type": "new"}
}

campaign_response = requests.post(
    "http://localhost:8008/api/marketing/email/campaigns",
    json=campaign_data,
    headers={"Authorization": "Bearer your-token"}
)

campaign = campaign_response.json()

# Send campaign
recipients = [{"email": "john.doe@company.com", "name": "John Doe"}]
send_response = requests.post(
    f"http://localhost:8008/api/marketing/email/campaigns/{campaign['id']}/send",
    json=recipients,
    headers={"Authorization": "Bearer your-token"}
)
```

### A/B Testing

```python
# Create A/B test experiment
experiment_data = {
    "name": "Button Color Test",
    "description": "Test different button colors for conversion",
    "hypothesis": "Red buttons will have higher conversion rates",
    "variants": [
        {"name": "Control", "variant_type": "control", "content": {"color": "blue"}},
        {"name": "Variant A", "variant_type": "variant", "content": {"color": "red"}}
    ],
    "primary_metric": "conversion_rate",
    "target_audience": {"user_type": "all"}
}

experiment_response = requests.post(
    "http://localhost:8008/api/marketing/ab-testing/experiments",
    json=experiment_data,
    headers={"Authorization": "Bearer your-token"}
)

experiment = experiment_response.json()

# Start the experiment
start_response = requests.post(
    f"http://localhost:8008/api/marketing/ab-testing/experiments/{experiment['id']}/start",
    headers={"Authorization": "Bearer your-token"}
)

# Get results
results_response = requests.get(
    f"http://localhost:8008/api/marketing/ab-testing/experiments/{experiment['id']}/results",
    headers={"Authorization": "Bearer your-token"}
)

results = results_response.json()
print(f"Experiment results: {results}")
```

## Testing

Run the test suite to ensure all functionality works correctly:

```bash
# Run all marketing service tests
pytest tests/unit/test_marketing_service.py -v

# Run specific test class
pytest tests/unit/test_marketing_service.py::TestLeadManager -v

# Run with coverage
pytest tests/unit/test_marketing_service.py --cov=src.marketing --cov-report=html
```

## Monitoring & Observability

The service includes comprehensive monitoring and observability features:

### Health Checks
- **Endpoint**: `/health`
- **Checks**: Database connectivity, Redis connectivity, service status
- **Response**: Service health status with component details

### Metrics (Prometheus)
- **Request counts**: Total requests, successful requests, failed requests
- **Response times**: Average, 95th percentile, 99th percentile
- **Business metrics**: Lead creation rate, email delivery rate, conversion rates

### Distributed Tracing (Jaeger)
- **Request tracing**: Track requests across service boundaries
- **Performance analysis**: Identify bottlenecks and slow operations
- **Error tracking**: Trace error paths and identify root causes

### Structured Logging
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Structured format**: JSON logging with consistent field names
- **Context information**: Request ID, user ID, correlation ID

## Security

### Authentication & Authorization
- **JWT tokens**: Secure authentication using JSON Web Tokens
- **Role-based access**: Different permission levels for different user roles
- **API key support**: Alternative authentication method for service-to-service communication

### Data Protection
- **Input validation**: Comprehensive validation of all input data
- **SQL injection prevention**: Parameterized queries and input sanitization
- **XSS protection**: HTML content sanitization and validation

### Rate Limiting
- **Request throttling**: Prevent abuse and ensure fair usage
- **IP-based limits**: Different limits for different client types
- **Configurable thresholds**: Adjustable rate limiting parameters

## Performance

### Caching Strategy
- **Redis caching**: Fast access to frequently used data
- **Template caching**: Cache compiled email templates
- **Query result caching**: Cache database query results

### Database Optimization
- **Connection pooling**: Efficient database connection management
- **Query optimization**: Optimized SQL queries with proper indexing
- **Batch operations**: Bulk operations for improved performance

### Async Processing
- **Non-blocking I/O**: Async/await pattern for better concurrency
- **Background tasks**: Process heavy operations asynchronously
- **Queue management**: Handle high-volume operations efficiently

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database URL and credentials
   - Verify database is running and accessible
   - Check network connectivity

2. **Redis Connection Issues**
   - Verify Redis server is running
   - Check Redis URL and authentication
   - Ensure Redis has sufficient memory

3. **Email Delivery Problems**
   - Verify SMTP credentials
   - Check email provider settings
   - Review email content for spam triggers

4. **Performance Issues**
   - Monitor database query performance
   - Check Redis memory usage
   - Review application logs for bottlenecks

### Debug Mode

Enable debug mode for detailed logging:

```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

### Log Analysis

Use structured logging for easier debugging:

```bash
# Filter logs by level
grep '"level":"ERROR"' logs/marketing-service.log

# Search for specific request
grep "request_id:abc123" logs/marketing-service.log

# Monitor performance
grep "duration_ms" logs/marketing-service.log | sort -n
```

## Contributing

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests for new functionality**
5. **Run the test suite**
6. **Submit a pull request**

### Code Standards

- **Python**: Follow PEP 8 style guidelines
- **Type hints**: Use type hints for all function parameters and return values
- **Documentation**: Include docstrings for all public functions and classes
- **Testing**: Maintain >90% test coverage

### Testing Guidelines

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test component interactions
- **Performance tests**: Ensure performance requirements are met
- **Security tests**: Verify security measures are effective

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- **Documentation**: Check this README and API documentation
- **Issues**: Report bugs and feature requests via GitHub issues
- **Discussions**: Join community discussions on GitHub
- **Email**: Contact the development team directly

## Roadmap

### Upcoming Features

- **AI-powered lead scoring**: Machine learning-based lead qualification
- **Advanced segmentation**: Behavioral and predictive segmentation
- **Multi-channel campaigns**: SMS, push notifications, and social media
- **Advanced analytics**: Predictive analytics and machine learning insights
- **Mobile app support**: Native mobile applications for marketing teams

### Performance Improvements

- **GraphQL API**: More efficient data fetching
- **Real-time updates**: WebSocket support for live data
- **Edge caching**: CDN integration for global performance
- **Database sharding**: Horizontal scaling for large datasets

### Integration Enhancements

- **More CRM providers**: Additional CRM system integrations
- **Marketing tools**: Integration with popular marketing platforms
- **Analytics platforms**: Google Analytics, Mixpanel, Amplitude
- **Social media**: Facebook, LinkedIn, Twitter advertising integration
