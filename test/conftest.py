from pathlib import Path
import pytest


@pytest.fixture
def btl_dir():
    return Path(__file__).parent / "bottlefile_test_data"
