from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from core.reader import read_uploaded_files
from core.fields import build_mapping
from core.cleaning import normalize_sheets

def test_cleaning_real_files():
    paths = [Path('/Users/Admin/Documents/Codex/项目/table_20261109.xlsx'), Path('/Users/Admin/Documents/Codex/项目/table_20261109(1).xlsx')]
    sheets = read_uploaded_files(paths)
    mappings = {(s.file_name, s.sheet_name): build_mapping(s) for s in sheets}
    result = normalize_sheets(sheets, mappings)
    assert len(result) == 13
    assert result['金额'].notna().sum() >= 6
    assert result['金额异常'].notna().sum() >= 3
