# Food Monster - Backend

## 项目说明

这是一个 FastAPI 后端应用，实现图片上传、获取和管理功能。

## 功能特性

- ✅ 图片上传 - 支持多种图片格式
- ✅ 自动记录上传时间 - 精确到毫秒
- ✅ 图片获取 - 按 ID 返回图片
- ✅ 图片列表 - 查看所有上传的图片
- ✅ 元数据管理 - 记录文件信息和上传时间

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

应用将在 `http://localhost:8000` 启动

## API 文档

访问 `http://localhost:8000/docs` 查看完整的 Swagger API 文档

访问 `http://localhost:8000/redoc` 查看 ReDoc 文档

## API 端点

### 1. 上传图片

**POST** `/api/upload`

请求体: multipart/form-data (file)

响应:

```json
{
  "status": "success",
  "filename": "20231219_120530_123456.jpg",
  "upload_time": "2023-12-19T12:05:30.123456",
  "file_size": 102400,
  "message": "图片上传成功"
}
```

### 2. 获取图片

**GET** `/api/image/{filename}`

返回: 图片文件

### 3. 获取图片列表

**GET** `/api/images`

响应:

```json
{
  "status": "success",
  "count": 2,
  "images": [
    {
      "filename": "20231219_120530_123456.jpg",
      "original_name": "photo.jpg",
      "upload_time": "2023-12-19T12:05:30.123456",
      "file_size": 102400,
      "download_url": "/api/image/20231219_120530_123456.jpg"
    }
  ]
}
```

### 4. 获取图片元数据

**GET** `/api/image/{filename}/metadata`

响应:

```json
{
  "status": "success",
  "filename": "20231219_120530_123456.jpg",
  "metadata": {
    "original_name": "photo.jpg",
    "upload_time": "2023-12-19T12:05:30.123456",
    "file_size": 102400,
    "content_type": "image/jpeg"
  }
}
```

## 目录结构

```
backend/
├── main.py              # FastAPI应用主文件
├── requirements.txt     # 依赖列表
├── README.md           # 本文件
└── uploads/            # 上传的图片存储目录
    └── metadata.json   # 图片元数据文件
```

## 特性说明

### 自动记录上传时间

- 每次上传图片时，后端会自动记录 ISO 格式的上传时间戳
- 元数据存储在 `uploads/metadata.json` 文件中
- 支持查询任意图片的上传时间

### 文件安全性

- 验证上传文件必须是图片格式
- 使用路径安全检查防止目录遍历
- 使用时间戳生成唯一文件名，防止覆盖

### CORS 支持

- 已启用 CORS 中间件，允许前端跨域请求
- 可配置允许的域名列表

## 测试

可以使用 curl 命令测试：

```bash
# 上传图片
curl -X POST "http://localhost:8000/api/upload" -F "file=@test.jpg"

# 获取图片列表
curl "http://localhost:8000/api/images"

# 获取图片
curl "http://localhost:8000/api/image/20231219_120530_123456.jpg" -o downloaded.jpg

# 获取元数据
curl "http://localhost:8000/api/image/20231219_120530_123456.jpg/metadata"
```

## 许可证

MIT
