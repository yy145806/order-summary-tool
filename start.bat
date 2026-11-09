@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 首次运行：正在创建运行环境并安装依赖，请稍候……
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)
echo 订单汇总工具正在启动，请打开 http://localhost:8501
.venv\Scripts\streamlit.exe run app.py
pause
