from abc import ABC
from dataclasses import dataclass
from typing import Generic, TypeVar

from chatapp_api_hex.domain.ports.unit_of_work import UnitOfWork

T = TypeVar("T")


@dataclass
class DomainService(Generic[T], ABC):
    """Base class for all domain services."""

    unit_of_work: UnitOfWork
