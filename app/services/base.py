"""Base services module."""
import shutil
from abc import ABC
from dataclasses import dataclass
from typing import ClassVar, Any, Generator

from fastapi import UploadFile, Depends
from sqlalchemy.orm import Session

from db import get_db
from exceptions import base as base_exceptions
from schemas.base import BaseModel


@dataclass
class BaseService(ABC):
    """
    Base service class with database operation for models.

    Inheriting class must override following fields: model.

    class SampleService(BaseService):
        model = SampleModel

    """
    model: ClassVar[Any]
    db: Session

    def _get_by_pk(self, pk: Any) -> Any:
        """Returns item with matching pk, or None if item is not found."""
        return self.db.query(self.model).get(pk)

    def all(self):
        """Returns list of all records."""
        return self.db.query(self.model).all()

    def get_or_404(self, pk: Any) -> Any:
        """Returns item with matching pk. If nothing found raises NotFound."""
        item = self._get_by_pk(pk)
        if item is None:
            raise base_exceptions.NotFound
        return item

    def create(self, schema: BaseModel) -> Any:
        """Creates and returns item."""
        item = self.model(**schema.dict())
        self.db.add(item)
        self.db.commit()
        return item

    def update(self, pk, schema: BaseModel) -> Any:
        """Updates and returns updated item."""
        item = self.get_or_404(pk)

        for field, value in schema.dict().items():
            if value is not None:
                setattr(item, field, value)

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, pk: Any) -> None:
        """Deletes item with given pk."""
        item = self.get_or_404(pk)
        self.db.delete(item)
        self.db.commit()


def upload_static_file(path: str, file: UploadFile) -> None:
    """Uploads file to given path"""
    with open(path, "wb") as fp:
        shutil.copyfileobj(file.file, fp)


def get_service(service: type(type(BaseService)), db: Session = Depends(get_db)
                ) -> Generator[BaseService, None, None]:
    """
    Base function for creating service dependency
    for using with fastapi dependency injection tool.
    Services give us a class with crud operations etc.
    with established db connection and settings.
    """
    yield service(db)
