"""订单文件读取逻辑，与 Streamlit 界面分离。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable

import pandas as pd


SUPPORTED_SUFFIXES = {".xlsx", ".xls"}
FIELD_ALIASES = {
    "订单号": {"订单号", "订单编号", "订单号", "交易单号"},
    "下单日期": {"下单日期", "下单时间", "订单创建时间"},
    "金额": {"金额", "订单金额", "实付金额", "买家实付金额"},
    "商品名称": {"商品名称", "商品标题", "商品名", "宝贝名称"},
    "平台": {"平台", "来源平台", "订单平台"},
    "退款/状态": {"订单状态", "退款状态", "状态"},
}


@dataclass
class SheetData:
    """一个工作表的读取结果。"""

    file_name: str
    sheet_name: str
    frame: pd.DataFrame
    headers: list[str]
    field_matches: dict[str, str]


def normalize_header(header: object) -> str:
    """标准化表头，去除首尾空白、换行并统一大小写。"""
    return " ".join(str(header).replace("\n", " ").replace("\r", " ").split()).casefold()


def recognize_fields(headers: list[str]) -> dict[str, str]:
    """按别名字典识别标准字段；歧义字段不静默选择，留给界面手动确认。"""
    normalized = {normalize_header(h): h for h in headers}
    matches: dict[str, str] = {}
    for standard, aliases in FIELD_ALIASES.items():
        candidates = [original for alias in aliases if (original := normalized.get(normalize_header(alias)))]
        if len(candidates) == 1:
            matches[standard] = candidates[0]
    return matches


def _read_excel(source: str | Path | BinaryIO, file_name: str) -> dict[str, pd.DataFrame]:
    """读取一个 Excel 文件的所有工作表，返回“工作表名 -> DataFrame”。"""
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"不支持的文件格式：{file_name}，仅支持 .xlsx 或 .xls")
    if suffix == ".xls":
        try:
            return pd.read_excel(source, sheet_name=None, engine="xlrd")
        except ImportError as exc:
            raise RuntimeError("读取 .xls 需要安装 xlrd：pip install xlrd") from exc
    try:
        return pd.read_excel(source, sheet_name=None, engine="openpyxl")
    except Exception as exc:
        # 有些平台会把 CSV 错误地命名为 .xlsx；明确标记为兼容读取。
        if hasattr(source, "seek"):
            source.seek(0)
        try:
            return {"CSV内容（扩展名错误）": pd.read_csv(source, encoding="utf-8")}
        except Exception:
            raise exc


def read_uploaded_files(files: Iterable[object]) -> list[SheetData]:
    """读取上传文件并保留文件名、工作表名、原始行数及表头。

    `files` 可为 Streamlit UploadedFile，也可为带 name 属性的文件对象。
    空工作表仍会返回，便于界面明确提示用户。
    """
    results: list[SheetData] = []
    for uploaded in files:
        file_name = str(getattr(uploaded, "name", "未命名文件"))
        try:
            if hasattr(uploaded, "seek"):
                uploaded.seek(0)
            sheets = _read_excel(uploaded, file_name)
        except Exception as exc:
            raise RuntimeError(f"文件“{file_name}”读取失败：{exc}") from exc
        for sheet_name, frame in sheets.items():
            headers = [str(column) for column in frame.columns]
            results.append(SheetData(file_name, str(sheet_name), frame, headers, recognize_fields(headers)))
    return results
