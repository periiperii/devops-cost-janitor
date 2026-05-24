# Submission — DevOps Engineer Assignment

**Candidate name:** Priyansi Patnaik  
**Email:** patnaikpriyansi05@gmail.com  
**Date submitted:** 2026-05-24  
**Hours spent (approximate):** 18–22 hours  

## Deliverables checklist

- [x] Part A: Terraform code under /terraform applies cleanly on LocalStack
- [x] Part A: `terraform validate` and `terraform fmt -check` both pass
- [x] Part B: Janitor script runs in --dry-run mode and produces report.json
- [x] Part B: GitHub Actions workflow runs green on a fresh PR
- [x] Part B: --delete mode respects Protected=true tag
- [x] Part C: DESIGN.md is present and within 2 pages
- [x] Walkthrough video link below is accessible (unlisted is fine)

## Walkthrough video
  
https://youtu.be/SMqVs5BKL6g

## Sample report

Path to a sample report.json produced by your script:

```text
samples/report.example.json
```

## Known limitations

- LocalStack does not fully emulate all AWS behaviors, especially S3 lifecycle execution semantics.
- Cost estimation values are simplified static estimates and not dynamically fetched from AWS Pricing APIs.
- The current implementation focuses only on a subset of AWS resources (EC2, EBS, Elastic IP, S3).
- Multi-account AWS scanning is not implemented.
- Delete workflows are intentionally conservative to reduce accidental destructive operations.
- GitHub Actions uploads artifacts even when janitor scans return non-zero exit codes so findings remain reviewable during CI runs.

## AI usage disclosure

AI tools used:
- ChatGPT for Terraform, LocalStack, and GitHub Actions debugging.
- GitHub Copilot for boilerplate autocomplete.

One AI suggestion that I changed:
- An early workflow version suppressed CI failures using `|| true`. I replaced this with safer handling that still uploads artifacts while preserving janitor exit behavior.

One section implemented manually:
- The orphan detection and delete safety logic were manually validated to ensure resource cleanup behavior remained predictable and safe.