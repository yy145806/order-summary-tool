"""订单疑似重复识别及可配置过滤。"""
from __future__ import annotations

import re
import pandas as pd


def normalize_product_name(value: object) -> str:
    """生成保守的商品匹配键：去首尾空白并折叠连续空白。"""
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def _is_refund(value: object) -> bool:
    return any(word in str(value or "") for word in ("退款", "退货", "已退款"))


def apply_deduplication(
    data: pd.DataFrame,
    *,
    retain_refunds: bool = True,
    retain_split_rows: bool = True,
) -> pd.DataFrame:
    """标记并按选项过滤疑似重复行，默认保留退款和拆单行。"""
    result = data.copy()
    result["商品匹配键"] = result["商品名称"].map(normalize_product_name)
    platform = result.get("平台", pd.Series("", index=result.index)).fillna("").astype(str)
    result["退款行"] = result.get("退款/状态", pd.Series("", index=result.index)).map(_is_refund)
    # 退款与销售分开比较，避免同一订单的退款行覆盖正常销售行。
    result["比较组"] = result["退款行"].map({True: "退款", False: "销售"})
    result["去重键"] = platform + "|" + result["订单号"].fillna("").astype(str) + "|" + result["商品匹配键"] + "|" + result["比较组"]
    result["疑似重复"] = result["去重键"].duplicated(keep=False) & result["订单号"].notna() & result["订单号"].ne("") & result["商品匹配键"].ne("")
    result["处理结果"] = "保留"
    result["处理原因"] = ""
    if not retain_refunds:
        mask = result["退款行"]
        result.loc[mask, "处理结果"] = "删除"
        result.loc[mask, "处理原因"] = "用户选择剔除退款行"
    if not retain_split_rows:
        candidate = result["疑似重复"] & (result["处理结果"] != "删除")
        # 保留每组第一行，删除其余同键行；退款行按上面的独立选项处理。
        duplicate_after_first = candidate & result.duplicated("去重键", keep="first")
        result.loc[duplicate_after_first, "处理结果"] = "删除"
        result.loc[duplicate_after_first, "处理原因"] = "用户选择不保留同订单同商品的重复行"
    return result


def kept_rows(data: pd.DataFrame) -> pd.DataFrame:
    """返回处理结果为“保留”的行。"""
    return data.loc[data["处理结果"].eq("保留")].copy()
