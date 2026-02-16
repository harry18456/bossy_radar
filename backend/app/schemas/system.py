from datetime import datetime

from pydantic import BaseModel


class SyncStatusItem(BaseModel):
    last_updated: datetime | None
    count: int


class SyncStatusResponse(BaseModel):
    companies: dict[str, SyncStatusItem]
    violations: dict[str, SyncStatusItem]
    environmental_violations: dict[str, SyncStatusItem]
    mops: dict[str, SyncStatusItem]
