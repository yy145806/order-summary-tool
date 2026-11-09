"""汇总统计与 Excel 导出。"""
from __future__ import annotations

from io import BytesIO
import pandas as pd


def build_statistics(data: pd.DataFrame) -> pd.DataFrame:
    """按最终保留明细计算总订单数、有效金额和各平台订单数。"""
    kept = data[data["处理结果"].eq("保留")] if "处理结果" in data else data
    valid_amount = kept["金额"].notna()
    order_key = kept["平台"].fillna("").astype(str) + "|" + kept["订单号"].fillna("").astype(str)
    valid_order = kept["订单号"].notna() & kept["订单号"].ne("")
    total_orders = order_key[valid_order].nunique()
    total_amount = kept.loc[valid_amount, "金额"].sum()
    refund_amount = kept.loc[valid_amount & kept["退款行"], "金额"].sum() if "退款行" in kept else 0
    rows = [
        {"统计项": "总订单数", "数值": int(total_orders), "备注": "按平台+订单号去重计数"},
        {"统计项": "有效金额合计（含退款）", "数值": round(float(total_amount), 2), "备注": "仅计入金额有效的保留行，已包含退款行"},
        {"统计项": "其中退款金额", "数值": round(float(refund_amount), 2), "备注": "退款行金额合计，已计入有效金额合计"},
        {"统计项": "异常金额行数", "数值": int((~valid_amount).sum()), "备注": "异常行仍保留在明细中"},
        {"统计项": "缺订单号行数", "数值": int((~valid_order).sum()), "备注": "单独报告，不计入订单数"},
        {"统计项": "疑似重复组数", "数值": int(data.loc[data["疑似重复"], "去重键"].nunique()) if "疑似重复" in data else 0, "备注": "按去重键计数"},
        {"统计项": "被剔除行数", "数值": int((data["处理结果"] == "删除").sum()) if "处理结果" in data else 0, "备注": "按本次删除选项统计"},
    ]
    for platform, group in kept.groupby("平台", dropna=False):
        platform_name = str(platform) if str(platform).strip() else "未识别平台"
        platform_key = group["平台"].fillna("").astype(str) + "|" + group["订单号"].fillna("").astype(str)
        note = "按平台+订单号去重计数" if platform_name != "未识别平台" else "源文件无平台列"
        rows.append({"统计项": f"平台订单数：{platform_name}", "数值": int(platform_key[group["订单号"].notna() & group["订单号"].ne("")].nunique()), "备注": note})
    return pd.DataFrame(rows)


def export_xlsx(data: pd.DataFrame, options: dict[str, object] | None = None) -> bytes:
    """导出汇总明细、统计和处理记录三个工作表，返回 XLSX 字节。"""
    output = BytesIO()
    stats = build_statistics(data)
    detail_columns = [c for c in data.columns if c not in {"商品匹配键", "去重键", "比较组"}]
    records = data[[c for c in ["来源文件", "来源工作表", "来源行号", "处理结果", "处理原因", "疑似重复"] if c in data.columns]]
    if options:
        option_rows = pd.DataFrame([{"记录类型": "本次选项", "字段": k, "内容": str(v)} for k, v in options.items()])
        records = pd.concat([option_rows, records.rename(columns={"来源文件": "字段"})], ignore_index=True, sort=False)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data[detail_columns].to_excel(writer, sheet_name="汇总明细", index=False)
        stats.to_excel(writer, sheet_name="统计", index=False)
        records.to_excel(writer, sheet_name="处理记录", index=False)
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cell in sheet[1]:
                cell.font = cell.font.copy(bold=True)
        detail = writer.book["汇总明细"]
        headers = {cell.value: cell.column for cell in detail[1]}
        if "金额" in headers:
            for cell in detail.iter_cols(min_col=headers["金额"], max_col=headers["金额"], min_row=2):
                for value_cell in cell:
                    value_cell.number_format = "0.00"
    return output.getvalue()
