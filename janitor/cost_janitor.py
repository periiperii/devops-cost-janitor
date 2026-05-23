import boto3
import json
import argparse
import sys
from datetime import datetime, timezone

from constants import (
    AWS_REGION,
    LOCALSTACK_ENDPOINT,
    REQUIRED_TAGS,
    EBS_PRICE_PER_GB,
    STOPPED_INSTANCE_DAYS
)

ec2_client = boto3.client(
    "ec2",
    region_name=AWS_REGION,
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)


def get_tag_dict(tags):
    if not tags:
        return {}

    return {tag["Key"]: tag["Value"] for tag in tags}


def is_protected(tags):
    return tags.get("Protected", "false").lower() == "true"


def find_unattached_volumes():
    response = ec2_client.describe_volumes()

    findings = []

    for volume in response["Volumes"]:
        tags = get_tag_dict(volume.get("Tags", []))

        if volume["State"] == "available":
            findings.append({
                "resource_id": volume["VolumeId"],
                "resource_type": "ebs_volume",
                "reason": "unattached",
                "age_days": 0,
                "estimated_monthly_cost_usd": round(
                    volume["Size"] * EBS_PRICE_PER_GB, 2
                ),
                "tags": tags,
                "suggested_action": "delete",
                "safe_to_auto_delete": not is_protected(tags)
            })

    return findings


def find_stopped_instances():
    response = ec2_client.describe_instances()

    findings = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:

            state = instance["State"]["Name"]

            if state == "stopped":

                tags = get_tag_dict(instance.get("Tags", []))

                findings.append({
                    "resource_id": instance["InstanceId"],
                    "resource_type": "ec2_instance",
                    "reason": f"stopped_more_than_{STOPPED_INSTANCE_DAYS}_days",
                    "age_days": STOPPED_INSTANCE_DAYS,
                    "estimated_monthly_cost_usd": 5.00,
                    "tags": tags,
                    "suggested_action": "review",
                    "safe_to_auto_delete": not is_protected(tags)
                })

    return findings


def find_unused_eips():
    response = ec2_client.describe_addresses()

    findings = []

    for address in response["Addresses"]:

        tags = get_tag_dict(address.get("Tags", []))

        if not address.get("InstanceId"):

            findings.append({
                "resource_id": address["AllocationId"],
                "resource_type": "elastic_ip",
                "reason": "unassociated",
                "age_days": 0,
                "estimated_monthly_cost_usd": 3.50,
                "tags": tags,
                "suggested_action": "release",
                "safe_to_auto_delete": not is_protected(tags)
            })

    return findings


def find_missing_tags():
    findings = []

    volume_response = ec2_client.describe_volumes()

    for volume in volume_response["Volumes"]:

        tags = get_tag_dict(volume.get("Tags", []))

        if tags.get("ManagedBy") != "terraform":
            continue

        missing_tags = [
            tag for tag in REQUIRED_TAGS
            if tag not in tags
        ]

        if missing_tags:

            findings.append({
                "resource_id": volume["VolumeId"],
                "resource_type": "ebs_volume",
                "reason": f"missing_tags: {', '.join(missing_tags)}",
                "age_days": 0,
                "estimated_monthly_cost_usd": 0,
                "tags": tags,
                "suggested_action": "add_tags",
                "safe_to_auto_delete": False
            })

    return findings


def delete_resource(finding):

    if not finding["safe_to_auto_delete"]:
        print(f"Skipping protected resource: {finding['resource_id']}")
        return

    resource_type = finding["resource_type"]

    if resource_type == "ebs_volume":

        ec2_client.delete_volume(
            VolumeId=finding["resource_id"]
        )

        print(f"Deleted volume: {finding['resource_id']}")

    elif resource_type == "elastic_ip":

        ec2_client.release_address(
            AllocationId=finding["resource_id"]
        )

        print(f"Released Elastic IP: {finding['resource_id']}")

    elif resource_type == "ec2_instance":

        ec2_client.terminate_instances(
            InstanceIds=[finding["resource_id"]]
        )

        print(f"Terminated instance: {finding['resource_id']}")


def generate_markdown_summary(report):

    lines = [
        "# Cost Janitor Summary",
        "",
        f"Total findings: {report['summary']['total_orphans']}",
        f"Estimated monthly waste: ${report['summary']['estimated_monthly_waste_usd']}",
        "",
        "## Findings",
        ""
    ]

    for finding in report["findings"]:
        lines.append(
            f"- {finding['resource_type']} "
            f"({finding['resource_id']}): "
            f"{finding['reason']}"
        )

    return "\n".join(lines)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete orphan resources"
    )

    args = parser.parse_args()

    if args.delete:
        print("DELETE MODE ENABLED")
    else:
        print("Running in DRY RUN mode")

    findings = []

    findings.extend(find_unattached_volumes())
    findings.extend(find_stopped_instances())
    findings.extend(find_unused_eips())
    findings.extend(find_missing_tags())

    total_waste = sum(
        finding["estimated_monthly_cost_usd"]
        for finding in findings
    )

    report = {
        "scan_timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "account_id": "000000000000",

        "region": AWS_REGION,

        "summary": {
            "total_orphans": len(findings),
            "estimated_monthly_waste_usd": round(total_waste, 2)
        },

        "findings": findings
    }

    with open("report.json", "w") as report_file:
        json.dump(report, report_file, indent=4)

    markdown_summary = generate_markdown_summary(report)

    with open("summary.md", "w") as summary_file:
        summary_file.write(markdown_summary)

    print(json.dumps(report, indent=4))

    if args.delete:
        for finding in findings:
            delete_resource(finding)

    if len(findings) > 0 and not args.delete:
        sys.exit(1)
