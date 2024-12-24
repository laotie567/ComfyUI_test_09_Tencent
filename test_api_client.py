import requests
import json
import time

def test_api():
    """测试API服务的各个端点"""
    base_url = "http://localhost:8080"
    
    print("1. 测试健康检查接口...")
    response = requests.get(f"{base_url}/health")
    print(f"健康检查结果: {response.json()}\n")

    print("2. 测试工作流执行...")
    # 完整的工作流示例
    workflow = {
        "workflow": {
            "1": {
                "inputs": {
                    "text": "a beautiful landscape",
                    "clip": ["clip", ""]
                },
                "class_type": "CLIPTextEncode"
            },
            "2": {
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "3": {
                "inputs": {
                    "samples": ["2", 0],
                    "text_embeddings": ["1", 0],
                    "seed": 42,
                    "steps": 20,
                    "cfg": 7,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["1", 0],
                    "negative": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {
                    "ckpt_name": "v1-5-pruned.ckpt"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {
                    "text": "text, watermark",
                    "clip": ["clip", ""]
                },
                "class_type": "CLIPTextEncode"
            },
            "6": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode"
            },
            "7": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["6", 0]
                },
                "class_type": "SaveImage"
            }
        },
        "client_id": "test_client"
    }
    
    response = requests.post(f"{base_url}/api/workflow/execute", json=workflow)
    result = response.json()
    print(f"工作流执行结果: {json.dumps(result, indent=2)}\n")

    if "prompt_id" in result:
        print("3. 测试工作流状态查询...")
        time.sleep(2)  # 等待一下让工作流开始执行
        status_response = requests.get(f"{base_url}/api/workflow/status/{result['prompt_id']}")
        print(f"工作流状态: {json.dumps(status_response.json(), indent=2)}\n")

    print("4. 测试队列状态查询...")
    queue_response = requests.get(f"{base_url}/api/workflow/queue")
    print(f"队列状态: {json.dumps(queue_response.json(), indent=2)}")

if __name__ == "__main__":
    test_api() 