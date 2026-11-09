"""字段确认业务逻辑。"""
from __future__ import annotations

from dataclasses import dataclass
from .reader import SheetData

REQUIRED_FIELDS = ("订单号", "下单日期", "金额", "商品名称")
OPTIONAL_FIELDS = ("平台", "退款/状态")


@dataclass
class FieldValidation:
    """字段映射校验结果。"""

    valid: bool
    errors: list[str]


def validate_field_mapping(mapping: dict[str, str | None], headers: list[str]) -> FieldValidation:
    """校验用户确认的字段映射，返回中文错误信息。"""
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        value = mapping.get(field)
        if not value:
            errors.append(f"缺少必填字段“{field}”，请选择对应列")
        elif value not in headers:
            errors.append(f"字段“{field}”指定的列“{value}”不存在")
    chosen = [v for v in mapping.values() if v]
    if len(chosen) != len(set(chosen)):
        errors.append("同一列不能同时指定给多个字段")
    return FieldValidation(not errors, errors)


def build_mapping(sheet: SheetData, overrides: dict[str, str | None] | None = None) -> dict[str, str | None]:
    """合并自动识别结果与用户手动指定结果。"""
    mapping = {field: sheet.field_matches.get(field) for field in (*REQUIRED_FIELDS, *OPTIONAL_FIELDS)}
    if overrides:
        mapping.update(overrides)
    return mapping
