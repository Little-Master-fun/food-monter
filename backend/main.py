from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import json
from pathlib import Path

app = FastAPI(title="Food Monster Backend", version="1.0.0")

# 添加CORS中间件，允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置上传文件保存路径
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 图片元数据文件路径
METADATA_FILE = UPLOAD_DIR / "metadata.json"

# 初始化元数据文件
def init_metadata():
    if not METADATA_FILE.exists():
        with open(METADATA_FILE, 'w') as f:
            json.dump({}, f)

init_metadata()


def load_metadata():
    """加载图片元数据"""
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)


def save_metadata(metadata):
    """保存图片元数据"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片接口
    - 接受图片文件
    - 自动记录上传时间
    - 返回图片ID和上传时间
    """
    try:
        # 验证文件类型
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只支持图片文件")
        
        # 生成文件名（使用时间戳确保唯一性）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        file_extension = Path(file.filename).suffix
        saved_filename = f"{timestamp}{file_extension}"
        file_path = UPLOAD_DIR / saved_filename
        
        # 保存文件
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # 记录上传时间和文件信息
        upload_time = datetime.now().isoformat()
        metadata = load_metadata()
        metadata[saved_filename] = {
            "original_name": file.filename,
            "upload_time": upload_time,
            "file_size": len(contents),
            "content_type": file.content_type
        }
        save_metadata(metadata)
        
        return {
            "status": "success",
            "filename": saved_filename,
            "upload_time": upload_time,
            "file_size": len(contents),
            "message": "图片上传成功"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.get("/api/image/{filename}")
async def get_image(filename: str):
    """
    获取图片接口
    - 返回指定filename的图片
    """
    try:
        file_path = UPLOAD_DIR / filename
        
        # 检查文件是否存在
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="图片不存在")
        
        # 验证文件在上传目录内（安全检查）
        if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
            raise HTTPException(status_code=403, detail="禁止访问")
        
        # 获取文件的content type
        metadata = load_metadata()
        content_type = metadata.get(filename, {}).get("content_type", "image/jpeg")
        
        return FileResponse(file_path, media_type=content_type)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@app.get("/api/images")
async def list_images():
    """
    获取所有上传的图片信息
    - 返回图片列表及其上传时间
    """
    try:
        metadata = load_metadata()
        images = []
        for filename, info in metadata.items():
            images.append({
                "filename": filename,
                "original_name": info.get("original_name"),
                "upload_time": info.get("upload_time"),
                "file_size": info.get("file_size"),
                "download_url": f"/api/image/{filename}"
            })
        
        return {
            "status": "success",
            "count": len(images),
            "images": images
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片列表失败: {str(e)}")


@app.get("/api/image/{filename}/metadata")
async def get_image_metadata(filename: str):
    """
    获取图片元数据
    - 返回图片的上传时间等信息
    """
    try:
        metadata = load_metadata()
        
        if filename not in metadata:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        return {
            "status": "success",
            "filename": filename,
            "metadata": metadata[filename]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取元数据失败: {str(e)}")


@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "Food Monster Backend API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /api/upload - 上传图片",
            "get_image": "GET /api/image/{filename} - 获取图片",
            "list_images": "GET /api/images - 获取所有图片列表",
            "get_metadata": "GET /api/image/{filename}/metadata - 获取图片元数据"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
