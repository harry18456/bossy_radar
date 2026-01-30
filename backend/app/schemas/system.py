from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel

class SyncStatusItem(BaseModel):
    last_updated: Optional[datetime]
    count: int

class SyncStatusResponse(BaseModel):
    companies: Dict[str, SyncStatusItem]
    violations: Dict[str, SyncStatusItem]
    mops: Dict[str, SyncStatusItem]
