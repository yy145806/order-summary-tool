# Excel 订单汇总工具

这是一个本地运行的 Excel 订单汇总工具。所有文件在本机 Python 进程中处理，不上传到服务器。

## 安装与启动

不会使用命令行时：

- macOS：双击 `start.command`。如果系统阻止打开，右键文件选择“打开”。
- Windows：双击 `start.bat`。

第一次双击会自动创建运行环境并安装依赖，可能需要等待几分钟；以后直接双击即可启动。

```bash
python -m venv .venv
source .venv/bin/activate       # Windows 使用 .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 Streamlit 显示的本地地址即可使用。

## 出错时

- 如果上传文件格式不支持，页面会显示具体文件名和原因。
- 如果文件扩展名是 `.xlsx`，但实际内容是 CSV，工具会提示“扩展名错误”，并按 CSV 兼容读取；建议重新导出为真正的 `.xlsx` 文件。
- 如果字段无法自动识别，可在“字段确认”区域手动指定。

## 测试

```bash
python -m pytest tests
```

`.xls` 文件由 `xlrd` 读取；`.xlsx` 文件由 `openpyxl` 读取。
