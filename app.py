"""Streamlit 一页式订单汇总工具：上传、确认、去重、预览与导出。"""
from __future__ import annotations

import streamlit as st

from core.fields import OPTIONAL_FIELDS, REQUIRED_FIELDS, build_mapping, validate_field_mapping
from core.reader import read_uploaded_files
from core.cleaning import normalize_sheets
from core.deduplication import apply_deduplication, kept_rows
from core.exporter import build_statistics, export_xlsx

st.set_page_config(page_title="订单汇总工具", page_icon="📦", layout="wide")
st.title("Excel 订单汇总工具")
st.caption("上传 → 字段确认 → 去重选项 → 预览与导出。文件只在本机处理。")

uploads = st.file_uploader("① 上传订单文件（可多选）", type=["xlsx", "xls", "csv"], accept_multiple_files=True)
if uploads:
    try:
        sheets = read_uploaded_files(uploads)
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()
    st.subheader("② 字段确认")
    confirmed = True
    mappings = {}
    for index, sheet in enumerate(sheets):
        st.markdown(f"**{sheet.file_name} / {sheet.sheet_name}**（{len(sheet.frame)} 行）")
        st.dataframe(sheet.frame.head(3), use_container_width=True, hide_index=True)
        options = ["（未指定）"] + sheet.headers
        defaults = build_mapping(sheet)
        mapping = {}
        cols = st.columns(3)
        for pos, field in enumerate((*REQUIRED_FIELDS, *OPTIONAL_FIELDS)):
            default = defaults.get(field)
            default_index = options.index(default) if default in options else 0
            with cols[pos % 3]:
                selected = st.selectbox(field, options, index=default_index, key=f"field_{index}_{field}")
            mapping[field] = None if selected == "（未指定）" else selected
        result = validate_field_mapping(mapping, sheet.headers)
        if not result.valid:
            confirmed = False
            for error in result.errors:
                st.warning(error)
        mappings[(sheet.file_name, sheet.sheet_name)] = mapping
    if confirmed:
        st.success("所有工作表的必填字段已确认，可以进入下一阶段。")
        st.session_state["field_mappings"] = mappings
        st.subheader("③ 去重选项")
        normalized = normalize_sheets(sheets, mappings)
        st.write(f"已合并 {len(normalized)} 行，来源信息已保留。")
        retain_split = st.checkbox("保留拆单/同键多行", value=True)
        retain_refunds = st.checkbox("保留退款行", value=True)
        processed = apply_deduplication(normalized, retain_refunds=retain_refunds, retain_split_rows=retain_split)
        duplicate_count = int(processed["疑似重复"].sum())
        st.info(f"疑似重复组涉及 {duplicate_count} 行；默认只标记，不自动删除。")
        if not retain_split or not retain_refunds:
            preview = processed[processed["处理结果"] == "删除"]
            if len(preview):
                st.warning(f"根据当前选项，将删除 {len(preview)} 行。请核对下方预览。")
                st.dataframe(preview[["来源文件", "来源工作表", "来源行号", "订单号", "商品名称", "退款/状态", "处理原因"]], use_container_width=True, hide_index=True)
            else:
                st.success("当前选项不会删除任何行。")
        if st.button("确认应用删除规则", disabled=retain_split and retain_refunds):
            st.session_state["merged_data"] = kept_rows(processed)
            st.success(f"已应用规则，保留 {len(st.session_state['merged_data'])} 行。")
        current = st.session_state.get("merged_data", kept_rows(processed) if retain_split and retain_refunds else None)
        if current is not None:
            st.subheader("④ 预览与导出")
            st.dataframe(build_statistics(current), use_container_width=True, hide_index=True)
            st.download_button("下载汇总 Excel", data=export_xlsx(current, {"保留拆单/同键多行": retain_split, "保留退款行": retain_refunds}), file_name="订单汇总.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("请先上传一个或多个订单文件。")
