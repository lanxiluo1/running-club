FROM python:3.11-slim

# 安装系统依赖（包括 Tesseract OCR）
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制后端代码
COPY backend/requirements.txt ./requirements.txt
COPY backend/ ./backend/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 8080

# 启动命令
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}
