# DevOps Cost Janitor

## Overview

DevOps Cost Janitor is a FinOps-focused infrastructure automation project that detects potentially wasteful AWS resources and generates actionable cost reports. The project provisions a simulated AWS environment using Terraform and LocalStack, then runs a Python-based janitor utility that scans for orphaned or non-compliant resources such as unattached EBS volumes, stopped EC2 instances, unused Elastic IPs, and resources missing mandatory governance tags.

The system supports both dry-run and delete modes, generates structured JSON and Markdown reports, uploads artifacts through GitHub Actions, and intentionally fails CI checks when orphaned resources are detected to simulate real-world governance enforcement workflows.

---

## How to run locally

### 1. Clone repository

```bash
git clone https://github.com/periiperii/devops-cost-janitor.git

cd devops-cost-janitor
```

> Make sure Docker Desktop is running before starting LocalStack.  
> The project was tested using Ubuntu on WSL2 with Docker Desktop integration enabled.

### 2. Start LocalStack

```bash
docker run -d \
  -p 4566:4566 \
  -e SERVICES=ec2,s3,ebs \
  --name localstack \
  localstack/localstack:3.5

sleep 15
```

Verify:

```bash
docker ps
```

---

### 3. Provision infrastructure

```bash
cd terraform

terraform init

terraform fmt -check

terraform validate

terraform apply -auto-approve
```

---

### 4. Install Python dependencies

```bash
cd ../janitor

pip install -r requirements.txt
```

---

### 5. Run janitor in dry-run mode

```bash
python3 cost_janitor.py
```

This:
- scans infrastructure,
- generates `report.json`,
- generates `summary.md`,
- exits with non-zero status if orphan resources are found.

---

### 6. Run janitor in delete mode

```bash
python3 cost_janitor.py --delete
```

Delete mode:
- removes orphan resources,
- skips anything tagged `Protected=true`.

---

### 7. Run tests

```bash
pytest
```

---

## Architecture

```text
                +----------------------+
                |   GitHub Actions     |
                |   CI/CD Workflow     |
                +----------+-----------+
                           |
                           v
                +----------------------+
                |      LocalStack      |
                |  AWS Cloud Emulator  |
                +----------+-----------+
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
+-------------------+          +----------------------+
| Terraform Infra   |          | Python Cost Janitor |
| VPC / EC2 / EBS   |          | boto3-based scanner |
| S3 / Elastic IP   |          | orphan detection    |
+-------------------+          +----------------------+
```

### Infrastructure Components

Terraform provisions:
- VPC
- Public subnets
- Route tables
- Internet gateway
- Security groups
- EC2 instances
- Orphan EBS volume
- Unused Elastic IP
- S3 bucket

The Python janitor utility scans the environment using boto3 APIs and generates governance reports.

GitHub Actions automates:
- Terraform provisioning,
- janitor execution,
- artifact uploads,
- PR summary comments.

---

## Decisions & deviations

- Used `if: always()` in GitHub Actions so reports upload and workflows remain reviewable even when janitor scans return non-zero exit codes, balancing artifact visibility with assignment requirements.
- Used LocalStack instead of moto because the assignment required Terraform-based infrastructure provisioning and end-to-end integration testing.
- Kept infrastructure intentionally minimal and assignment-focused instead of adding unnecessary networking complexity.

---

## Trade-offs

With more time, I would add:
- scheduled scans,
- Slack/email alerts,
- richer cost estimation,
- remote Terraform state with locking,
- support for more AWS resource types,
- safer automated remediation workflows.

---

## AI usage disclosure

AI tools used:
- ChatGPT for Terraform, LocalStack, and GitHub Actions debugging.
- GitHub Copilot for boilerplate autocomplete.

One AI suggestion that I changed:
- An early workflow version suppressed CI failures using `|| true`. I replaced this with safer handling that still uploads artifacts while preserving janitor exit behavior.

One part implemented manually:
- The orphan detection and delete safety logic were manually validated to ensure resource cleanup behavior remained predictable and safe.