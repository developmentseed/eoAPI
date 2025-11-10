---
title: "AWS CDK Deployment"
description: "Serverless deployment of eoAPI on AWS using CDK"
external_links:
  - name: "eoapi-cdk Repository"
    url: "https://github.com/developmentseed/eoapi-cdk"
  - name: "eoapi-template Repository"
    url: "https://github.com/developmentseed/eoapi-template"
---

# AWS CDK Deployment

[← Back to Deployment](../../deployment.md)

Serverless deployment of eoAPI on AWS using Lambda, RDS, and API Gateway.

## Architecture

eoAPI on AWS CDK provides:
- AWS Lambda functions for API services
- Amazon RDS PostgreSQL database
- API Gateway for routing and management
- CloudFormation for infrastructure as code
- Automatic scaling based on request volume
- Pay-per-request pricing model

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured
- Node.js 14+
- Python 3.8+
- AWS CDK CLI

## Quick Start

1. **Clone and Setup**
```bash
git clone https://github.com/developmentseed/eoapi-template.git
cd eoapi-template

python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm install
```

2. **Configure**
```bash
# Copy and edit configuration
cp config.yaml.example config.yaml
# Edit config.yaml with your settings
```

3. **Bootstrap CDK** (one-time per AWS account)
```bash
PROJECT_ID=eoAPI STAGE=staging npx cdk bootstrap
```

4. **Deploy**
```bash
PROJECT_ID=eoAPI STAGE=staging npx cdk deploy vpceoAPI-staging eoAPI-staging
```

## Configuration

The deployment is configured through `config.yaml` and environment variables:

- `PROJECT_ID`: Prefix for stack names
- `STAGE`: Environment name (staging, production, etc.)
- Database settings, Lambda configuration, and API Gateway options

See [configuration examples](https://github.com/developmentseed/eoapi-template/blob/main/config.yaml.example) for detailed options.

## Components

- **[eoapi-cdk](https://github.com/developmentseed/eoapi-cdk)** - CDK constructs library
- **[eoapi-template](https://github.com/developmentseed/eoapi-template)** - Example CDK application

## Troubleshooting

**VPC Limits**: If you encounter "max VPCs reached" errors, switch to a different AWS region.

**Permissions**: Ensure your AWS credentials have permissions for Lambda, RDS, API Gateway, and CloudFormation.