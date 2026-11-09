from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from core.fields import validate_field_mapping

def test_mapping_validation():
    headers = ["订单号", "日期", "金额", "商品"]
    result = validate_field_mapping({"订单号":"订单号", "下单日期":"日期", "金额":"金额", "商品名称":"商品"}, headers)
    assert result.valid

def test_missing_required_field():
    result = validate_field_mapping({}, ["订单号"])
    assert not result.valid
    assert any("金额" in error for error in result.errors)
