# =============================================================================
# app/domain/models/base.py
# =============================================================================
from abc import ABC
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4


class DomainEntity(ABC):
    """Base class for all domain entities."""

    def __init__(self, id: Optional[UUID] = None):
        self.id = id or uuid4()
        now = datetime.now(timezone.utc)
        self.created_at = now
        self.updated_at = now

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
