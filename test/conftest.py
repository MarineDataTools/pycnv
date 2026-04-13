import pathlib
import pytest


@pytest.fixture
def btl_dir():
    return pathlib.Path(__file__).parent / "bottlefile_test_data"
