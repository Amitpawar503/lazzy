"""Extract plain text, skills, and a target-role hint from an uploaded resume.

Supports PDF (pdfminer.six), DOCX (python-docx), and plain text. Skill/role
extraction is heuristic; when AI is enabled the AI layer can refine it, but this
keeps upload working with zero API keys.
"""
from __future__ import annotations

import io
import re

# A pragmatic skills dictionary — extend freely. Matching is case-insensitive
# and word-boundary aware so "go" doesn't match "google".
SKILL_VOCAB = [
    "python", "java", "javascript", "typescript", "go", "golang", "rust", "c++",
    "c#", "ruby", "php", "scala", "kotlin", "swift",
    "react", "angular", "vue", "next.js", "node.js", "node", "express", "django",
    "flask", "fastapi", "spring", "spring boot", "rails", ".net",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "nosql",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd", "jenkins",
    "kafka", "rabbitmq", "graphql", "rest", "grpc", "microservices",
    "machine learning", "deep learning", "nlp", "pytorch", "tensorflow", "pandas",
    "numpy", "scikit-learn", "llm", "data science", "spark", "airflow",
    "html", "css", "tailwind", "sass", "redux",
    "product management", "agile", "scrum", "figma", "ui/ux",
]

ROLE_HINTS = [
    "software engineer", "senior software engineer", "staff engineer",
    "backend engineer", "frontend engineer", "full stack developer",
    "full-stack developer", "data scientist", "data engineer",
    "machine learning engineer", "devops engineer", "site reliability engineer",
    "product manager", "engineering manager", "solution architect",
    "technical architect", "lead developer", "principal engineer",
]


def extract_text(filename: str, content: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _pdf_text(content)
    if name.endswith(".docx"):
        return _docx_text(content)
    # Fallback: treat as utf-8 text.
    try:
        return content.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _pdf_text(content: bytes) -> str:
    try:
        from pdfminer.high_level import extract_text as pdf_extract
        return pdf_extract(io.BytesIO(content)) or ""
    except Exception:
        return ""


def _docx_text(content: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_skills(text: str) -> list[str]:
    low = text.lower()
    found = []
    for skill in SKILL_VOCAB:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, low):
            found.append(skill)
    # de-dupe while preserving order
    seen = set()
    out = []
    for s in found:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def infer_title(text: str) -> str:
    low = text.lower()
    # Prefer the longest role phrase that appears (more specific wins).
    matches = [r for r in ROLE_HINTS if r in low]
    if matches:
        return max(matches, key=len).title()
    # Fallback: first non-empty line that isn't obviously a name/email.
    for line in text.splitlines():
        s = line.strip()
        if 3 < len(s) < 60 and "@" not in s and not s.replace(" ", "").isalpha() is False:
            return s
    return ""


def parse_resume(filename: str, content: bytes) -> dict:
    text = extract_text(filename, content)
    return {
        "text": text.strip(),
        "skills": ", ".join(extract_skills(text)),
        "title_hint": infer_title(text),
    }
