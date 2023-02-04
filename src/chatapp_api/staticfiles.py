"""Module with staticfiles manager base and implementation classes."""
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from urllib import parse

from fastapi import UploadFile


class BaseStaticFilesManager(ABC):
    """
    Base class for staticfiles managers.
    Child classes must implement all its abstract methods.
    """

    static_domain: str
    static_url: str

    def get_url(self, path: str):
        """Returns joined path with staticfiles url."""
        return parse.urljoin(self.static_url, path)

    @abstractmethod
    def load(self, path: str, file: UploadFile) -> None:
        """Load file to the target path"""


@dataclass
class LocalStaticFilesManager(BaseStaticFilesManager):
    """Local static files handler. Uses local machines storage."""

    static_domain: str
    static_url: str
    static_root: Path

    def load(self, path: str, file: UploadFile):
        """Uploads file to given path"""
        full_path = self.static_root / path
        full_path.mkdir(exist_ok=True, parents=True)
        file_path = full_path / file.filename

        with open(file_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
