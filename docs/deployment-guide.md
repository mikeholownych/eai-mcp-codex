# Deployment Guide

This guide provides instructions for deploying the MCP Microservices project to a variety of environments.

## Docker Compose

The easiest way to deploy the project is with Docker Compose. The project includes `docker-compose.yml` and `docker-compose.prod.yml` files for development and production environments, respectively.

To deploy the project with Docker Compose, run the following command:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes

The project also includes a Helm chart for deploying to Kubernetes. To deploy the project with Helm, run the following command:

```bash
helm install mcp-a2a ./helm/mcp-a2a-services
```

## Production Environment

In a production environment, it is recommended to use a managed Kubernetes service, such as Amazon EKS, Google GKE, or Azure AKS. The project includes a `production-guide.md` file with detailed instructions for deploying to a production environment.
