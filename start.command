#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -x ".venv/bin/python" ]; then
  echo "首次运行：正在创建运行环境并安装依赖，请稍候……"
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi
echo "订单汇总工具正在启动，浏览器会打开 http://localhost:8501"
.venv/bin/streamlit run app.py
