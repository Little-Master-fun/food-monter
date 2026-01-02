# Food Monster - Backend

## 项目说明

这是一个 FastAPI 后端应用，实现图片上传、获取和管理功能。

## 功能特性

- ✅ 图片上传 - 支持多种图片格式
- ✅ 自动记录上传时间 - 精确到毫秒
- ✅ 图片获取 - 按 ID 返回图片
- ✅ 图片列表 - 查看所有上传的图片
- ✅ 元数据管理 - 记录文件信息和上传时间
- ✅ **AI 食物识别** - 使用 OpenAI 兼容 API 自动识别食物并获取营养信息

## 配置说明

### 环境变量配置

1. 复制 `.env.example` 为 `.env`:

   ```bash
   copy .env.example .env
   ```

2. 在 `.env` 文件中配置你的 OpenAI API 密钥和相关设置:

   ```
   OPENAI_API_KEY=your_actual_api_key
   OPENAI_BASE_URL=https://yunwu.zeabur.app
   OPENAI_MODEL=gpt-5.1
   USE_VISION_API=false
   ```

   **重要说明**：

   - 如果你的 API 支持图片识别（如 GPT-4V、DeepSeek-VL 等），请设置 `USE_VISION_API=true`
   - 如果你的 API 不支持图片输入，请设置 `USE_VISION_API=false`（将返回占位数据）
   - 对于完整的食物识别功能，建议使用支持多模态的 API

3. 获取 API 密钥:
   - 从你的 AI 服务提供商获取 API 密钥
   - 配置相应的 base_url 和 model 参数

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

### 1. 上传图片（含 AI 食物识别）

**POST** `/api/upload`

请求体: multipart/form-data (file)

响应:

```json
{
  "status": "success",
  "filename": "20231219_120530_123456.jpg",
  "upload_time": "2023-12-19T12:05:30.123456",
  "file_size": 102400,
  "food_recognition": {
    "success": true,
    "food_name": "宫保鸡丁",
    "description": "一道经典的川菜，由鸡肉丁、花生米、干辣椒等炒制而成，色泽红亮，口味酸甜微辣",
    "nutrition": {
      "protein": "18.5",
      "carbohydrates": "12.3",
      "fat": "15.8",
      "vitamins": ["维生素A", "维生素C", "维生素E"],
      "calories": "280",
      "fiber": "2.5"
    }
  },
  "message": "图片上传并识别成功"
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

### 4. 获取图片元数据（含食物识别信息）

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
    "content_type": "image/jpeg",
    "food_recognition": {
      "success": true,
      "food_name": "宫保鸡丁",
      "description": "一道经典的川菜...",
      "nutrition": {
        "protein": "18.5",
        "carbohydrates": "12.3",
        "fat": "15.8",
        "vitamins": ["维生素A", "维生素C", "维生素E"],
        "calories": "280",
        "fiber": "2.5"
      }
    }
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

### AI 食物识别

- 使用 OpenAI 兼容的 API 自动识别上传的食物图片
- 支持自定义 API 端点和模型配置
- **支持两种模式**：
  - **视觉模式**（USE_VISION_API=true）：使用支持多模态的 API 进行真实的图片识别
  - **降级模式**（USE_VISION_API=false）：当 API 不支持图片时返回占位数据
- 自动提取：
  - 食物名称（中文）
  - 食物详细描述（外观、烹饪方式等）
  - 营养数据（蛋白质、碳水化合物、脂肪、维生素、热量、膳食纤维）
- 识别结果自动保存到元数据中

**推荐的支持视觉的 API**：

- OpenAI GPT-4 Vision (gpt-4-vision-preview)
- DeepSeek-VL
- Claude 3 with vision
- Google Gemini Pro Vision

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
