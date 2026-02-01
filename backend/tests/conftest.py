import os
from pathlib import Path

import pytest


def reset_settings(tmp_path: Path):
    os.environ["DATA_DIR"] = str(tmp_path)
    os.environ["CORS_ORIGINS"] = "http://localhost:5173"

    from app.utils import config
    from app.db import session
    from app.services import container

    config.get_settings.cache_clear()
    session.get_engine.cache_clear()
    session.get_sessionmaker.cache_clear()
    container.get_index.cache_clear()
    container.get_embedder.cache_clear()
    container.get_llm.cache_clear()


@pytest.fixture()
def temp_data_dir(tmp_path):
    reset_settings(tmp_path)
    return tmp_path
