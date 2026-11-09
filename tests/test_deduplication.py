from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from core.reader import read_uploaded_files
from core.fields import build_mapping
from core.cleaning import normalize_sheets
from core.deduplication import apply_deduplication, kept_rows

def test_default_retains_split_rows():
    paths = [Path('/Users/Admin/Documents/Codex/项目/table_20261109.xlsx'), Path('/Users/Admin/Documents/Codex/项目/table_20261109(1).xlsx')]
    sheets = read_uploaded_files(paths)
    mappings = {(s.file_name, s.sheet_name): build_mapping(s) for s in sheets}
    data = normalize_sheets(sheets, mappings)
    result = apply_deduplication(data)
    assert len(kept_rows(result)) == 13
    assert result['疑似重复'].sum() == 0  # 同订单不同商品不应误判

def test_can_remove_duplicate_key_rows():
    import pandas as pd
    data = pd.DataFrame({'订单号':['1','1'], '商品名称':[' A ','A'], '平台':['P','P'], '退款/状态':['','']})
    result = apply_deduplication(data, retain_split_rows=False)
    assert len(kept_rows(result)) == 1
