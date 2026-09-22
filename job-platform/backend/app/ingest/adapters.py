"""Concrete ingest adapters.

Each `fetch_*` function is an async callable taking an httpx.AsyncClient plus
provider-specific args and returning a list[RawJob]. Grouped in one module so
the registry can map provider name -> function easily.

Sources covered:
  - greenhouse : boards-api.greenhouse.io   (thousands of companies' career pages)
  - lever      : api.lever.co               (many startups' career pages)
  - ashby      : api.ashbyhq.com            (modern startups' career pages)
  - remotive   : remotive.com/api           (aggregated remote jobs)
  - remoteok   : remoteok.com/api           (aggregated remote jobs)

These are public JSON endpoints — the same data those career pages render. We
never scrape rendered HTML or bypass auth.
"""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from .base import RawJob, SourceError, strip_html

UA = "CareerHound/0.1 (+https://example.local) job-aggregator"


def _iso_to_dt(value) -> datetime | None:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            # Lever uses epoch millis; Greenhouse uses ISO strings.
            secs = value / 1000 if value > 10_000_000_000 else value
            return datetime.fromtimestamp(secs, tz=timezone.utc)
        s = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except (ValueError, OSError, OverflowError):
        return None


async def _get_json(client: httpx.AsyncClient, url: str, **kw):
    try:
        resp = await client.get(url, headers={"User-Agent": UA, "Accept": "application/json"}, **kw)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, ValueError) as e:  # ValueError = bad JSON
        raise SourceError(f"{url}: {e}") from e


# --------------------------------------------------------------------------- #
# Greenhouse
# --------------------------------------------------------------------------- #
async def fetch_greenhouse(client: httpx.AsyncClient, slug: str, limit: int = 500) -> list[RawJob]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    data = await _get_json(client, url)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out: list[RawJob] = []
    for j in jobs[:limit]:
        loc = (j.get("location") or {}).get("name", "") if isinstance(j.get("location"), dict) else ""
        offices = ", ".join(o.get("name", "") for o in (j.get("offices") or []) if o.get("name"))
        location = loc or offices
        out.append(RawJob(
            source="greenhouse",
            external_id=f"{slug}:{j.get('id')}",
            title=j.get("title", "").strip(),
            company=slug.replace("-", " ").title(),
            company_slug=slug,
            apply_url=j.get("absolute_url", ""),
            location_raw=location,
            description=strip_html(j.get("content", ""))[:8000],
            category=_department(j),
            posted_at=_iso_to_dt(j.get("updated_at") or j.get("first_published")),
        ))
    return out


def _department(j: dict) -> str:
    deps = j.get("departments") or []
    if deps and isinstance(deps, list):
        return deps[0].get("name", "")
    return ""


# --------------------------------------------------------------------------- #
# Lever
# --------------------------------------------------------------------------- #
async def fetch_lever(client: httpx.AsyncClient, slug: str, limit: int = 500) -> list[RawJob]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    data = await _get_json(client, url)
    if not isinstance(data, list):
        raise SourceError("lever: unexpected payload")
    out: list[RawJob] = []
    for j in data[:limit]:
        cats = j.get("categories") or {}
        location = cats.get("location", "")
        workplace = j.get("workplaceType", "")  # "remote" | "on-site" | "hybrid"
        out.append(RawJob(
            source="lever",
            external_id=f"{slug}:{j.get('id')}",
            title=j.get("text", "").strip(),
            company=slug.replace("-", " ").title(),
            company_slug=slug,
            apply_url=j.get("hostedUrl", "") or j.get("applyUrl", ""),
            location_raw=location,
            description=strip_html(j.get("descriptionPlain") or j.get("description", ""))[:8000],
            category=cats.get("team", "") or cats.get("department", ""),
            posted_at=_iso_to_dt(j.get("createdAt")),
            source_remote=(workplace.lower() == "remote") if workplace else None,
        ))
    return out


# --------------------------------------------------------------------------- #
# Ashby
# --------------------------------------------------------------------------- #
async def fetch_ashby(client: httpx.AsyncClient, slug: str, limit: int = 500) -> list[RawJob]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    data = await _get_json(client, url)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out: list[RawJob] = []
    for j in jobs[:limit]:
        comp = j.get("compensation") or {}
        salary_raw = ""
        summary = comp.get("compensationTierSummary") if isinstance(comp, dict) else None
        if summary:
            salary_raw = str(summary)
        out.append(RawJob(
            source="ashby",
            external_id=f"{slug}:{j.get('id')}",
            title=j.get("title", "").strip(),
            company=j.get("organizationName") or slug.replace("-", " ").title(),
            company_slug=slug,
            apply_url=j.get("jobUrl", "") or j.get("applyUrl", ""),
            location_raw=j.get("location", "") or j.get("locationName", ""),
            description=strip_html(j.get("descriptionHtml") or j.get("descriptionPlain", ""))[:8000],
            category=j.get("department", "") or j.get("team", ""),
            salary_raw=salary_raw,
            posted_at=_iso_to_dt(j.get("publishedAt") or j.get("updatedAt")),
            source_remote=bool(j.get("isRemote")) if "isRemote" in j else None,
        ))
    return out


# --------------------------------------------------------------------------- #
# Remotive (aggregated remote board)
# --------------------------------------------------------------------------- #
async def fetch_remotive(client: httpx.AsyncClient, search: str = "", limit: int = 500) -> list[RawJob]:
    url = "https://remotive.com/api/remote-jobs"
    params = {"limit": str(limit)}
    if search:
        params["search"] = search
    data = await _get_json(client, url, params=params)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out: list[RawJob] = []
    for j in jobs[:limit]:
        out.append(RawJob(
            source="remotive",
            external_id=str(j.get("id")),
            title=j.get("title", "").strip(),
            company=j.get("company_name", ""),
            company_slug=(j.get("company_name") or "").lower().replace(" ", "-"),
            apply_url=j.get("url", ""),
            location_raw=j.get("candidate_required_location", "Remote"),
            description=strip_html(j.get("description", ""))[:8000],
            category=j.get("category", ""),
            salary_raw=j.get("salary", ""),
            posted_at=_iso_to_dt(j.get("publication_date")),
            source_remote=True,
        ))
    return out


# --------------------------------------------------------------------------- #
# RemoteOK (aggregated remote board)
# --------------------------------------------------------------------------- #
async def fetch_remoteok(client: httpx.AsyncClient, limit: int = 500) -> list[RawJob]:
    url = "https://remoteok.com/api"
    data = await _get_json(client, url)
    if not isinstance(data, list):
        raise SourceError("remoteok: unexpected payload")
    out: list[RawJob] = []
    # First element is a legal/metadata notice — skip entries without an id.
    for j in data:
        if not isinstance(j, dict) or not j.get("id"):
            continue
        tags = j.get("tags") or []
        out.append(RawJob(
            source="remoteok",
            external_id=str(j.get("id")),
            title=j.get("position", "") or j.get("title", ""),
            company=j.get("company", ""),
            company_slug=(j.get("company") or "").lower().replace(" ", "-"),
            apply_url=j.get("url", "") or j.get("apply_url", ""),
            location_raw=j.get("location", "") or "Remote",
            description=strip_html(j.get("description", ""))[:8000],
            category=tags[0] if tags else "",
            salary_raw=_remoteok_salary(j),
            posted_at=_iso_to_dt(j.get("date")),
            source_remote=True,
        ))
        if len(out) >= limit:
            break
    return out


def _remoteok_salary(j: dict) -> str:
    lo, hi = j.get("salary_min"), j.get("salary_max")
    if lo and hi:
        return f"${lo:,} - ${hi:,}"
    return ""


# Map provider name -> (callable, wants_slug)
PROVIDERS = {
    "greenhouse": (fetch_greenhouse, True),
    "lever": (fetch_lever, True),
    "ashby": (fetch_ashby, True),
    "remotive": (fetch_remotive, False),
    "remoteok": (fetch_remoteok, False),
}
