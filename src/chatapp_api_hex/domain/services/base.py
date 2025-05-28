from abc import ABC
from dataclasses import dataclass

from chatapp_api_hex.domain.ports.unit_of_work import UnitOfWork


@dataclass
class DomainService[T](ABC):
    """Base class for all domain services."""

    unit_of_work: UnitOfWork
