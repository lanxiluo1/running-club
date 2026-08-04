FROM python:3.11-slim

# 安装系统依赖（包括 Tesseract OCR）
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
