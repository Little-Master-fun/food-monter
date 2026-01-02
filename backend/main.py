from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import json
from pathlib import Path
import base64
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(title="Food Monster Backend", version="1.0.0")

# 初始化OpenAI客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://yunwu.zeabur.app/v1")
)

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


def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为base64字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


async def recognize_food_with_ai(image_path: str) -> dict:
    """
    使用AI API识别食物
    返回食物名称、描述和营养数据
    支持多模态和纯文本两种模式
    """
    try:
        # 检查API是否支持视觉模型
        model = os.getenv("OPENAI_MODEL", "gpt-5.1")
        use_vision = os.getenv("USE_VISION_API", "false").lower() == "true"
        
        if use_vision:
            # 使用多模态API（支持图片输入）
            base64_image = encode_image_to_base64(image_path)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": """请识别这张图片中的食物，并以JSON格式返回以下信息。所有营养数据必须是数字类型，不要带单位：
{
  "food_name": "食物名称（中文）",
  "description": "食物的详细描述（包括外观、烹饪方式等）",
  "estimated_weight": 估计的食物重量（克，纯数字），
  "nutrition_per_100g": {
    "protein": 蛋白质含量（克/100克，纯数字），
    "carbohydrates": 碳水化合物含量（克/100克，纯数字），
    "fat": 脂肪含量（克/100克，纯数字），
    "calories": 热量（千卡/100克，纯数字），
    "fiber": 膳食纤维（克/100克，纯数字），
    "sodium": 钠含量（毫克/100克，纯数字），
    "sugar": 糖含量（克/100克，纯数字）
  },
  "vitamins": ["维生素A", "维生素C", "维生素E"]  // 主要维生素列表
}

注意：
1. 所有营养数据必须是纯数字，不要包含单位
2. estimated_weight是估计这份食物的总重量（克）
3. 请只返回JSON格式的数据，不要添加其他说明文字
4. 如果图片中没有食物，请返回 {"error": "未识别到食物"}

示例：
{
  "food_name": "宫保鸡丁",
  "description": "一道经典川菜...",
  "estimated_weight": 250,
  "nutrition_per_100g": {
    "protein": 18.5,
    "carbohydrates": 12.3,
    "fat": 15.8,
    "calories": 280,
    "fiber": 2.5,
    "sodium": 450,
    "sugar": 8.2
  },
  "vitamins": ["维生素A", "维生素C", "维生素E"]
}"""
                            }
                        ]
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # 检查响应类型
            if isinstance(response, str):
                # 如果API直接返回字符串
                content = response
            elif hasattr(response, 'choices') and len(response.choices) > 0:
                # 标准OpenAI格式响应
                content = response.choices[0].message.content.strip()
            elif isinstance(response, dict):
                # 如果返回字典格式
                if 'choices' in response and len(response['choices']) > 0:
                    content = response['choices'][0]['message']['content'].strip()
                elif 'content' in response:
                    content = response['content']
                elif 'text' in response:
                    content = response['text']
                else:
                    return {
                        "success": False,
                        "error": f"无法解析API响应格式: {type(response).__name__}",
                        "raw_response": str(response)[:500]
                    }
            else:
                return {
                    "success": False,
                    "error": f"未知的API响应类型: {type(response).__name__}",
                    "raw_response": str(response)[:500]
                }
        else:
            # 降级方案：返回模拟数据（当API不支持视觉时）
            # 实际项目中可以集成OCR + 文本识别，或者使用其他视觉API
            return {
                "success": True,
                "food_name": "未知食物",
                "description": "由于当前API不支持图片识别，无法提供详细描述。建议使用支持视觉的API模型。",
                "estimated_weight": 0,
                "nutrition_per_100g": {
                    "protein": 0,
                    "carbohydrates": 0,
                    "fat": 0,
                    "calories": 0,
                    "fiber": 0,
                    "sodium": 0,
                    "sugar": 0
                },
                "vitamins": [],
                "note": "当前API不支持图片识别，请在.env中设置USE_VISION_API=true并使用支持多模态的API"
            }
        
        # 尝试解析JSON（去除可能的markdown代码块标记）
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        result = json.loads(content)
        
        # 检查是否识别到食物
        if "error" in result:
            return {
                "success": False,
                "error": result["error"]
            }
        
        # 确保营养数据是数字类型
        nutrition = result.get("nutrition_per_100g", {})
        estimated_weight = result.get("estimated_weight", 0)
        
        # 转换为数字（防止AI返回字符串）
        def to_float(value, default=0):
            try:
                return float(value) if value else default
            except (ValueError, TypeError):
                return default
        
        nutrition_per_100g = {
            "protein": to_float(nutrition.get("protein", 0)),
            "carbohydrates": to_float(nutrition.get("carbohydrates", 0)),
            "fat": to_float(nutrition.get("fat", 0)),
            "calories": to_float(nutrition.get("calories", 0)),
            "fiber": to_float(nutrition.get("fiber", 0)),
            "sodium": to_float(nutrition.get("sodium", 0)),
            "sugar": to_float(nutrition.get("sugar", 0))
        }
        
        # 计算总营养（基于估计重量）
        weight_factor = to_float(estimated_weight) / 100
        total_nutrition = {
            "protein": round(nutrition_per_100g["protein"] * weight_factor, 1),
            "carbohydrates": round(nutrition_per_100g["carbohydrates"] * weight_factor, 1),
            "fat": round(nutrition_per_100g["fat"] * weight_factor, 1),
            "calories": round(nutrition_per_100g["calories"] * weight_factor, 1),
            "fiber": round(nutrition_per_100g["fiber"] * weight_factor, 1),
            "sodium": round(nutrition_per_100g["sodium"] * weight_factor, 1),
            "sugar": round(nutrition_per_100g["sugar"] * weight_factor, 1)
        }
        
        return {
            "success": True,
            "food_name": result.get("food_name", "未知食物"),
            "description": result.get("description", ""),
            "estimated_weight": to_float(estimated_weight),
            "nutrition_per_100g": nutrition_per_100g,
            "total_nutrition": total_nutrition,
            "vitamins": result.get("vitamins", [])
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"解析AI响应失败: {str(e)}",
            "raw_response": content if 'content' in locals() else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"食物识别失败: {str(e)}"
        }


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
        now = datetime.now()
        upload_time = now.isoformat()
        upload_date = now.strftime("%Y-%m-%d")  # 添加日期字段便于筛选
        metadata = load_metadata()
        
        # 使用AI识别食物
        food_info = await recognize_food_with_ai(str(file_path))
        
        # 保存元数据（包括食物识别信息）
        metadata[saved_filename] = {
            "original_name": file.filename,
            "upload_time": upload_time,
            "upload_date": upload_date,
            "file_size": len(contents),
            "content_type": file.content_type,
            "food_recognition": food_info
        }
        save_metadata(metadata)
        
        return {
            "status": "success",
            "filename": saved_filename,
            "upload_time": upload_time,
            "file_size": len(contents),
            "food_recognition": food_info,
            "message": "图片上传并识别成功" if food_info.get("success") else "图片上传成功，但食物识别失败"
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
        
        # 按上传时间倒序排序
        images.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
        
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


@app.get("/api/nutrition/daily/{date}")
async def get_daily_nutrition(date: str):
    """
    获取指定日期的总营养数据
    - date: 日期格式 YYYY-MM-DD
    - 返回当天所有食物的总营养数据
    """
    try:
        metadata = load_metadata()
        
        # 初始化总营养数据
        total = {
            "protein": 0,
            "carbohydrates": 0,
            "fat": 0,
            "calories": 0,
            "fiber": 0,
            "sodium": 0,
            "sugar": 0
        }
        
        foods_count = 0
        foods_list = []
        
        # 遍历所有图片，筛选指定日期的
        for filename, info in metadata.items():
            upload_date = info.get("upload_date", "")
            
            if upload_date == date:
                food_rec = info.get("food_recognition", {})
                
                # 只统计识别成功的食物
                if food_rec.get("success"):
                    total_nutrition = food_rec.get("total_nutrition", {})
                    
                    # 累加营养数据
                    for key in total.keys():
                        total[key] += total_nutrition.get(key, 0)
                    
                    foods_count += 1
                    foods_list.append({
                        "filename": filename,
                        "food_name": food_rec.get("food_name", "未知"),
                        "upload_time": info.get("upload_time", ""),
                        "estimated_weight": food_rec.get("estimated_weight", 0),
                        "total_nutrition": total_nutrition
                    })
        
        # 四舍五入到1位小数
        for key in total.keys():
            total[key] = round(total[key], 1)
        
        return {
            "status": "success",
            "date": date,
            "foods_count": foods_count,
            "total_nutrition": total,
            "foods": foods_list
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取每日营养失败: {str(e)}")


@app.get("/api/nutrition/summary")
async def get_nutrition_summary():
    """
    获取营养数据汇总
    - 返回最近7天的每日营养统计
    """
    try:
        from datetime import timedelta
        
        metadata = load_metadata()
        today = datetime.now().date()
        
        # 生成最近7天的日期列表
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        
        summary = []
        
        for date in dates:
            daily_total = {
                "protein": 0,
                "carbohydrates": 0,
                "fat": 0,
                "calories": 0,
                "fiber": 0,
                "sodium": 0,
                "sugar": 0
            }
            
            foods_count = 0
            
            # 统计该日期的营养数据
            for filename, info in metadata.items():
                upload_date = info.get("upload_date", "")
                
                if upload_date == date:
                    food_rec = info.get("food_recognition", {})
                    
                    if food_rec.get("success"):
                        total_nutrition = food_rec.get("total_nutrition", {})
                        
                        for key in daily_total.keys():
                            daily_total[key] += total_nutrition.get(key, 0)
                        
                        foods_count += 1
            
            # 四舍五入
            for key in daily_total.keys():
                daily_total[key] = round(daily_total[key], 1)
            
            summary.append({
                "date": date,
                "foods_count": foods_count,
                "total_nutrition": daily_total
            })
        
        return {
            "status": "success",
            "summary": summary
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取营养汇总失败: {str(e)}")


@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "Food Monster Backend API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /api/upload - 上传图片并自动识别食物",
            "get_image": "GET /api/image/{filename} - 获取图片",
            "list_images": "GET /api/images - 获取所有图片列表",
            "get_metadata": "GET /api/image/{filename}/metadata - 获取图片元数据（包括食物识别信息）",
            "daily_nutrition": "GET /api/nutrition/daily/{date} - 获取指定日期的总营养（日期格式: YYYY-MM-DD）",
            "nutrition_summary": "GET /api/nutrition/summary - 获取最近7天的营养汇总"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
