"""
测试脚本 - 用于测试FastAPI后端功能
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_upload():
    """测试图片上传"""
    print("=" * 50)
    print("测试1: 上传图片")
    print("=" * 50)
    
    # 创建一个测试图片（1x1 像素的红色PNG）
    test_image_path = Path("test_image.png")
    
    # PNG最小有效文件
    png_data = bytes([
        137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82,
        0, 0, 0, 1, 0, 0, 0, 1, 8, 2, 0, 0, 0, 144, 119, 83, 222, 0,
        0, 0, 12, 73, 68, 65, 84, 8, 215, 99, 248, 207, 192, 0, 0, 3,
        1, 1, 0, 24, 204, 137, 229, 0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130
    ])
    
    with open(test_image_path, "wb") as f:
        f.write(png_data)
    
    try:
        with open(test_image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result.get("filename") if response.status_code == 200 else None
    
    except Exception as e:
        print(f"错误: {e}")
        return None
    
    finally:
        test_image_path.unlink(missing_ok=True)


def test_list_images():
    """测试获取图片列表"""
    print("\n" + "=" * 50)
    print("测试2: 获取图片列表")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/images")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"错误: {e}")


def test_get_image(filename):
    """测试获取图片"""
    if not filename:
        print("\n跳过测试3: 没有有效的filename")
        return
    
    print("\n" + "=" * 50)
    print("测试3: 获取图片")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/image/{filename}")
        print(f"状态码: {response.status_code}")
        print(f"内容类型: {response.headers.get('content-type')}")
        print(f"文件大小: {len(response.content)} 字节")
    
    except Exception as e:
        print(f"错误: {e}")


def test_get_metadata(filename):
    """测试获取元数据"""
    if not filename:
        print("\n跳过测试4: 没有有效的filename")
        return
    
    print("\n" + "=" * 50)
    print("测试4: 获取图片元数据")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/image/{filename}/metadata")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"错误: {e}")


def test_root():
    """测试根路由"""
    print("\n" + "=" * 50)
    print("测试0: API信息")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    print("开始测试FastAPI后端...\n")
    print(f"目标地址: {BASE_URL}\n")
    
    # 首先检查服务器是否运行
    try:
        test_root()
        filename = test_upload()
        test_list_images()
        test_get_image(filename)
        test_get_metadata(filename)
        print("\n" + "=" * 50)
        print("测试完成！")
        print("=" * 50)
    
    except requests.exceptions.ConnectionError:
        print(f"错误: 无法连接到 {BASE_URL}")
        print("请确保服务器正在运行: python main.py")
