"""Module for testing functions from utils.py"""
import pytest

from src.chatapp_api import utils


@pytest.mark.parametrize(
    "path, expected",
    [
        (
            "C:\\Windows\\Temp\\some_file.txt",
            ("C:", "Windows", "Temp", "some_file.txt"),
        ),
        (
            r"C:\Windows\Temp\some_file.txt",
            ("C:", "Windows", "Temp", "some_file.txt"),
        ),
        ("/home/user/some_file.txt", ("home", "user", "some_file.txt")),
    ],
)
def test_split_path(path, expected):
    """Tests split path functions from utils module."""
    assert utils.split_path(path) == expected


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("hello.py", ("hello", "py")),
        ("hello.world.py", ("hello.world", "py")),
        (".gitignore", (".gitignore", ".")),
    ],
)
def test_split_filename(filename, expected):
    """Tests split filename functions from utils module."""
    assert utils.split_filename(filename) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            (
                "postgresql+psycopg2:"
                "//someuser:somepassword@localhost:5432/somedb"
            ),
            {
                "hostname": "localhost",
                "port": 5432,
                "user": "someuser",
                "password": "somepassword",
                "dbname": "somedb",
            },
        ),
        (
            "mysql://someuser:somepassword@localhost:3306/somedb",
            {
                "hostname": "localhost",
                "port": 3306,
                "user": "someuser",
                "password": "somepassword",
                "dbname": "somedb",
            },
        ),
    ],
)
def test_parse_url(url, expected):
    """Tests parse url function from utils module."""
    assert utils.parse_url(url) == expected
