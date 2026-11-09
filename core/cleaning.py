"""订单数据标准化与校验逻辑。"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable

import pandas as pd

from .fields import REQUIRED_FIELDS
from .reader import SheetData


def clean_amount(value: object) -> tuple[float | None, str | None]:
    """清洗金额，返回(数值, 异常说明)。无法明确判断时不强行提取数字。"""
    if pd.isna(value) or str(value).strip() == "":
        return None, "金额为空"
    text = str(value).strip().replace("，", ",")
    if re.search(r"[待约左右]|退款", text):
        return None, f"金额格式无法确认：{text}"
    normalized = re.sub(r"^(人民币|RMB|CNY|¥|￥)\s*", "", text, flags=re.I)
    if not re.fullmatch(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?|[-+]?\d+(?:\.\d+)?", normalized):
        return None, f"金额格式无法确认：{text}"
    try:
        amount = Decimal(normalized.replace(",", "")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None, f"金额格式无法确认：{text}"
    return float(amount), None


def _normalize_order(value: object) -> str | None:
    if pd.isna(value) or str(value).strip() == "":
        return None
    return str(value).strip()


def normalize_sheet(sheet: SheetData, mapping: dict[str, str | None]) -> pd.DataFrame:
    """按字段映射标准化一个工作表，并添加来源及校验列。"""
    missing = [field for field in REQUIRED_FIELDS if not mapping.get(field)]
    if missing:
        raise ValueError(f"{sheet.file_name}/{sheet.sheet_name} 缺少字段：{', '.join(missing)}")
    frame = sheet.frame.copy()
    result = pd.DataFrame(index=frame.index)
    result["订单号"] = frame[mapping["订单号"]].map(_normalize_order)
    result["下单日期"] = pd.to_datetime(frame[mapping["下单日期"]], errors="coerce")
    result["商品名称"] = frame[mapping["商品名称"]].where(frame[mapping["商品名称"]].notna(), "").astype(str).str.strip()
    amounts = frame[mapping["金额"]].map(clean_amount)
    result["原始金额"] = frame[mapping["金额"]]
    result["金额"] = amounts.map(lambda item: item[0])
    result["金额校验说明"] = amounts.map(lambda item: item[1])
    result["金额异常"] = result["金额校验说明"]
    platform_col = mapping.get("平台")
    status_col = mapping.get("退款/状态")
    result["平台"] = frame[platform_col].astype(str).str.strip() if platform_col else ""
    result["退款/状态"] = frame[status_col].astype(str).str.strip() if status_col else ""
    result["日期异常"] = result["下单日期"].isna().map(lambda bad: "日期为空或无法识别" if bad else None)
    result["来源文件"] = sheet.file_name
    result["来源工作表"] = sheet.sheet_name
    result["来源行号"] = frame.index + 2
    result["订单号异常"] = result["订单号"].isna().map(lambda bad: "订单号为空" if bad else None)
    return result.reset_index(drop=True)


def normalize_sheets(sheets: Iterable[SheetData], mappings: dict[tuple[str, str], dict[str, str | None]]) -> pd.DataFrame:
    """合并多个工作表的标准化结果。"""
    frames = [normalize_sheet(sheet, mappings[(sheet.file_name, sheet.sheet_name)]) for sheet in sheets]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
