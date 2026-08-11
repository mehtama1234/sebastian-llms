from __future__ import annotations

import pytest

from llm_dev_2026.corpus import build_default_benchmark


@pytest.fixture()
def bench():
    return build_default_benchmark()
