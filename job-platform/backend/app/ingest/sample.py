"""Offline sample jobs for local development / demos.

Lets you exercise the full stack (filters, tabs, matching, streaming, resume
enhancement) without any outbound network access. In production you rely on the
real adapters (greenhouse/lever/ashby/remotive/remoteok) instead. Loaded via
POST /api/sources/load-sample.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .base import RawJob

_NOW = datetime.now(timezone.utc)


def _sample_raws() -> list[RawJob]:
    data = [
        ("Senior Software Engineer - Backend", "Freshworks", "Remote - India",
         "Build scalable Python and FastAPI microservices on AWS with PostgreSQL and Kafka.",
         "Software", "₹25,00,000 - ₹40,00,000", True, 1),
        ("Full Stack Developer (React + Node)", "Zomato", "Gurgaon, India (Hybrid)",
         "React, TypeScript and Node.js. Flexible / work from home friendly. Delhi NCR based.",
         "Software", "₹18,00,000 - ₹30,00,000", False, 2),
        ("Staff Frontend Engineer", "Vercel", "Remote (Worldwide)",
         "Next.js, React, TypeScript. Fully remote, work from anywhere.",
         "Software", "$180,000 - $240,000", True, 0),
        ("Machine Learning Engineer", "Scale AI", "Remote - US",
         "PyTorch, LLMs, NLP. Deploy models at scale. Remote within the United States.",
         "Data Science", "$190,000 - $260,000", True, 3),
        ("Backend Engineer (Python)", "Postman", "Noida, India",
         "Django and FastAPI services. Hybrid, work from home options for Delhi NCR candidates.",
         "Software", "₹22,00,000 - ₹35,00,000", False, 1),
        ("DevOps Engineer", "Razorpay", "Bengaluru, India",
         "Kubernetes, Terraform, AWS, CI/CD pipelines. On-site.",
         "Infrastructure", "₹20,00,000 - ₹32,00,000", False, 5),
        ("Product Manager - Payments", "Stripe", "Remote - India",
         "Own payments product roadmap. Remote India role. Agile, cross-functional.",
         "Product", "₹35,00,000 - ₹55,00,000", True, 2),
        ("Senior Data Engineer", "Swiggy", "Remote (India)",
         "Spark, Airflow, Kafka, SQL. Build data platform. Work from home.",
         "Data Science", "₹28,00,000 - ₹45,00,000", True, 4),
        ("React Native Developer", "Groww", "Gurugram, India (Flexible)",
         "React Native, TypeScript, Redux. Flexible WFH in Delhi NCR.",
         "Software", "₹16,00,000 - ₹26,00,000", False, 6),
        ("Principal Engineer - Platform", "GitLab", "Remote - EMEA",
         "Go, Ruby, distributed systems. Fully remote outside India.",
         "Software", "$200,000 - $280,000", True, 1),
        ("SRE / Site Reliability Engineer", "Cloudflare", "Remote - India",
         "Kubernetes, Go, observability, incident response. Remote India.",
         "Infrastructure", "₹30,00,000 - ₹48,00,000", True, 3),
        ("Java Solution Architect", "NatWest Group", "Noida, India",
         "Spring Boot, microservices, AWS. Hybrid work from home for NCR.",
         "Software", "₹40,00,000 - ₹60,00,000", False, 2),
    ]
    raws = []
    for i, (title, company, loc, desc, cat, sal, remote, days_ago) in enumerate(data):
        raws.append(RawJob(
            source="sample",
            external_id=f"sample-{i}",
            title=title,
            company=company,
            company_slug=company.lower().replace(" ", "-"),
            apply_url=f"https://example.com/apply/sample-{i}",
            location_raw=loc,
            description=desc,
            category=cat,
            salary_raw=sal,
            posted_at=_NOW - timedelta(days=days_ago),
            source_remote=remote,
        ))
    return raws


def load_sample_jobs() -> int:
    from .pipeline import _persist, _broadcast_new

    inserted = _persist(_sample_raws())
    if inserted:
        _broadcast_new(inserted)
    return len(inserted)
