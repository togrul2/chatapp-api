import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from urllib import parse

from config import STATIC_DOMAIN, STATIC_ROOT, STATIC_URL
from fastapi import UploadFile


class BaseStaticFilesManager(ABC):
    static_domain: str
    static_url: str

    def get_url(self, path: str):
        return parse.urljoin(self.static_url, path)

    @abstractmethod
    def load(self, path: str, file: UploadFile) -> None:
        """Load file to the target path"""

    @abstractmethod
    def collect_staticfiles(self) -> None:
        """Collects static files into storage"""


@dataclass
class LocalStaticFilesManager(BaseStaticFilesManager):
    """Local static files handler. Uses local machines storage."""

    static_domain: str
    static_url: str
    static_root: Path | str

    def load(self, path: str, file: UploadFile):
        """Uploads file to given path"""
        full_path = self.static_root / path
        full_path.mkdir(exist_ok=True, parents=True)
        file_path = full_path / file.filename

        with open(file_path, "wb") as fp:
            shutil.copyfileobj(file.file, fp)

    def collect_staticfiles(self):
        pass


def get_staticfiles_manager():
    """Dependency for staticfiles"""
    yield LocalStaticFilesManager(STATIC_DOMAIN, STATIC_URL, STATIC_ROOT)
