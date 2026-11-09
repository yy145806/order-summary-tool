from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from core.reader import read_uploaded_files
from core.fields import build_mapping
from core.cleaning import normalize_sheets
from core.deduplication import apply_deduplication, kept_rows
from core.exporter import build_statistics, export_xlsx

def test_export_has_content():
    paths = [Path('/Users/Admin/Documents/Codex/项目/table_20261109.xlsx'), Path('/Users/Admin/Documents/Codex/项目/table_20261109(1).xlsx')]
    sheets = read_uploaded_files(paths)
    mappings = {(s.file_name, s.sheet_name): build_mapping(s) for s in sheets}
    data = kept_rows(apply_deduplication(normalize_sheets(sheets, mappings)))
    stats = build_statistics(data)
    blob = export_xlsx(data)
    assert len(blob) > 1000
    assert "总订单数" in stats["统计项"].tolist()
