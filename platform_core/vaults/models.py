from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class VaultLevel(str, Enum):
    PERSONAL = "personal"
    ROLE = "role"
    TEAM = "team"
    ORGANIZATION = "organization"

@dataclass
class VaultRecord:
    id: str
    vault_level: VaultLevel
    tenant_id: str
    record_type: str  # workflow|pattern|knowledge|process
    content: dict
    metadata: dict = field(default_factory=dict)
    contributor_hash: str = ""
    created_at: int = 0
    approved_by: Optional[str] = None
    approved_at: Optional[int] = None
    status: str = "approved"

@dataclass
class ContributionRequest:
    id: str
    from_vault: VaultLevel
    to_vault: VaultLevel
    record_id: str
    contributor_hash: str
    summary: str
    tenant_id: str
    created_at: int
    status: str = "pending"
    resolved_at: Optional[int] = None
