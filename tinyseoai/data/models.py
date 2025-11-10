from __future__ import annotations
from pydantic import BaseModel

class Issue(BaseModel):
    url: str
    type: str
    severity: str = "low"
    detail: str | None = None

class AuditResult(BaseModel):
    site: str
    pages_scanned: int
    issues: list[Issue]
    meta: dict
