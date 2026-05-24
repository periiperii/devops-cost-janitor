# Design Notes

## Multi-cloud reality

To support GCP and later Azure without rewriting the entire Janitor, the project should be structured around provider-specific adapters with a shared scanning core.

The current implementation tightly couples AWS boto3 calls with detection logic. In a production-grade multi-cloud system, the design would be refactored into separate layers:

```text
+-----------------------------+
|        Core Engine          |
|-----------------------------|
| Scan orchestration          |
| Report generation           |
| Cost aggregation            |
| Policy evaluation           |
+--------------+--------------+
               |
    +----------+----------+
    |                     |
    v                     v
+-----------+      +-------------+
| AWS Layer |      | GCP Layer   |
|-----------|      |-------------|
| boto3     |      | google sdk  |
| EC2 scan  |      | GCE scan    |
| EBS scan  |      | Disk scan   |
| EIP scan  |      | IP scan     |
+-----------+      +-------------+
                            |
                            v
                     +-------------+
                     | Azure Layer |
                     |-------------|
                     | azure sdk   |
                     | VM scan     |
                     | Disk scan   |
                     | IP scan     |
                     +-------------+
```

The core engine should only understand generic concepts such as:
- compute instances,
- unattached storage,
- unused public IPs,
- missing governance tags.

Each cloud adapter would translate provider-specific APIs into a normalized internal schema.

Example normalized finding:

```json
{
  "resource_type": "disk",
  "cloud_provider": "gcp",
  "attached": false,
  "monthly_cost_usd": 12.5
}
```

This design avoids rewriting detection logic every time a new cloud provider is added.

---

## Permissions

The Janitor requires different permission scopes depending on operating mode.

### Dry-run mode

Dry-run mode only requires:
- read-only inventory access,
- tag inspection access,
- metadata inspection access.

No mutation or delete permissions should be granted.

### Delete mode

Delete mode additionally requires:
- volume deletion,
- Elastic IP release,
- instance termination,
- tag updates (if remediation tagging is added later).

The delete-mode role should be separate from the dry-run role to reduce blast radius.

---

## Minimal IAM policy for read-only mode

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2ReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeAddresses",
        "ec2:DescribeTags",
        "ec2:DescribeNetworkInterfaces"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketTagging",
        "s3:GetLifecycleConfiguration"
      ],
      "Resource": "*"
    }
  ]
}
```

The policy intentionally excludes:
- delete actions,
- modify actions,
- IAM access,
- write permissions.

This follows least-privilege principles.

---

## Safety net

### Failure mode 1 — Deleting a stopped but business-critical EC2 instance

A stopped EC2 instance may appear unused but could actually be:
- a disaster recovery server,
- a month-end finance system,
- a manually paused production dependency.

Naïve auto-deletion could permanently remove important EBS-backed state.

Guardrails:
- require minimum inactivity age thresholds,
- skip resources tagged `Protected=true`,
- require approval workflow before deleting compute resources,
- add notification-based review before destructive operations.

---

### Failure mode 2 — Deleting unattached EBS volumes still used for backup recovery

An unattached EBS volume might be intentionally retained as:
- forensic evidence,
- backup snapshot staging,
- rollback recovery storage.

Blind deletion could destroy recovery data.

Guardrails:
- snapshot before deletion,
- quarantine mode before permanent deletion,
- retention-period enforcement,
- exclusion tags such as `Retention=Required`.

---

## Observability

The FinOps team needs visibility into whether the Janitor is actively finding waste, deleting resources safely, and behaving correctly over time.

| Metric | Source | Alert Threshold |
|---|---|---|
| orphan_resources_detected_total | Janitor scan results | >20 orphan resources |
| estimated_monthly_waste_usd | Report aggregation | >$500 projected waste |
| janitor_scan_duration_seconds | GitHub Actions workflow runtime | >10 minutes |
| deletion_failures_total | Delete operation logs | >3 failures per scan |
| protected_resources_skipped_total | Janitor delete workflow | Sudden spike >50 |

### Metric destinations

Metrics would ideally be published to:
- CloudWatch,
- Prometheus,
- Grafana dashboards,
- Slack alert integrations.

GitHub Actions logs alone are insufficient for long-term operational visibility.

---

## What you did not build

The implementation intentionally did not include aggressive automatic deletion workflows for all resource types. For example, stopped EC2 instances currently require review-oriented handling instead of unconditional termination because compute resources can still contain important business workloads.

Similarly, the project does not yet implement:
- automatic snapshot creation before EBS deletion,
- approval workflows before destructive actions,
- scheduled recurring scans,
- multi-account AWS scanning,
- Slack/email alert integrations,
- historical cost trend storage,
- support for additional AWS services such as RDS snapshots or idle load balancers.

These features were intentionally left out to keep the project focused on:
- safe orphan detection,
- reproducible infrastructure provisioning,
- CI/CD automation,
- governance-oriented reporting,
- assignment-aligned operational safety.

Given additional time, the next priority would be adding safer automated remediation workflows with rollback and approval mechanisms.