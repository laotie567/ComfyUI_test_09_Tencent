import requests

def test_comfyui_connection():
    """测试ComfyUI服务连接"""
    base_url = "http://43.153.201.167:6889"  # 你的ComfyUI服务地址
    print(f"正在测试连接到 ComfyUI 服务: {base_url}")
    
    try:
        # 测试队列接口
        response = requests.get(f"{base_url}/queue")
        if response.status_code == 200:
            print("✓ 成功连接到 ComfyUI 服务!")
            print("队列状态:", response.json())
            return True
    except Exception as e:
        print("✗ 连接失败:", str(e))
        return False

if __name__ == "__main__":
    test_comfyui_connection() 