from pathlib import Path

import pytest


@pytest.fixture
def templates_dir():
    return Path(__file__).parent.parent / "templates"


@pytest.fixture
def generated_agents_dir():
    return Path(__file__).parent.parent / "generated_agents"


@pytest.fixture
def pricing_monitor_path(generated_agents_dir):
    return generated_agents_dir / "pricing-monitor"
