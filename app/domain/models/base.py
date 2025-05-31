# =============================================================================
# app/domain/models/base.py
# =============================================================================
from abc import ABC
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


class DomainEntity(ABC):
    """Base class for all domain entities."""

    def __init__(self, id: Optional[UUID] = None):
        self.id = id or uuid4()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
