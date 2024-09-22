FROM python:3.9-slim

WORKDIR /app

# 安装SQLite和其他必要的包
RUN apt-get update && apt-get install -y sqlite3 curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY static /app/static

EXPOSE 5001

ENV PYTHONUNBUFFERED=1

# 创建一个目录来存储数据库文件
RUN mkdir -p /data

# 添加一个健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5001/health || exit 1

CMD ["python", "api.py"]