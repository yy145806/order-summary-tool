from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1]))
from core.reader import read_uploaded_files


def test_read_fixtures():
    fixtures = sorted((Path(__file__).parent / "fixtures").glob("*.xlsx"))
    results = read_uploaded_files(fixtures)
    assert results
    assert any(item.sheet_name == "退款与脏数据" for item in results)
    assert all(item.headers for item in results)
