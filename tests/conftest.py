from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.scales import Scale, load_scales

FIXTURE_SCALES = Path(__file__).parent / "fixtures" / "scales" 

@pytest.fixture
def client():
    """A client for a fresh app with an in-memory database"""
    app = create_app(Settings(database_url="sqlite://", scales_dir=FIXTURE_SCALES))

    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mini_scale() -> Scale:
    return load_scales(FIXTURE_SCALES)["ipip-mini"]