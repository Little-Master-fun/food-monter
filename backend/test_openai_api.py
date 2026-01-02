"""
测试 OpenAI API 配置
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_openai_connection():
    """测试 OpenAI API 连接"""
    try:
        # 初始化客户端
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://yunwu.zeabur.app")
        )

        print("API 配置信息:")
        print(f"- Base URL: {os.getenv('OPENAI_BASE_URL', 'https://yunwu.zeabur.app')}")
        print(f"- Model: {os.getenv('OPENAI_MODEL', 'gpt-5.1')}")
        print(f"- API Key: {os.getenv('OPENAI_API_KEY')[:10]}..." if os.getenv('OPENAI_API_KEY') else "未配置")

        # 测试简单的文本请求
        print("\n正在测试 API 连接...")
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.1"),
            messages=[
                {"role": "system", "content": "你是一个测试助手"},
                {"role": "user", "content": "请回复'API连接成功'"}
            ],
            temperature=0.1,
            max_tokens=50
        )

        print(f"\n✅ API 连接成功!")
        print(f"响应: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"\n❌ API 连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("OpenAI API 配置测试")
    print("=" * 50)
    test_openai_connection()