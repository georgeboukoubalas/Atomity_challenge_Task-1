from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from enum import Enum

class Eligibility(str, Enum):
    ELIGIBLE = "eligible"
    EXCLUDED = "excluded"
    VERIFICATION_REQUIRED = "verification_required"

class InputRecord(BaseModel):
    id: str
    url: HttpUrl
    publisher: str
    source_type: str
    publication_date: Optional[str] = None
    provenance: List[str] = Field(default_factory=list)

class NormalizedRecord(BaseModel):
    source_id: str
    canonical_url: str
    publisher: str
    source_type: str
    publication_date: Optional[str] = None
    event_date: Optional[str] = None
    discovery_lineage: List[str] = Field(default_factory=list)
    eligibility: Optional[Eligibility] = None
    reason_codes: List[str] = Field(default_factory=list)