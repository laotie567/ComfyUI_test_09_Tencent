import pytest
from fastapi.testclient import TestClient
import os
import time
from comfyui_service import app

client = TestClient(app)

# 跳过集成测试如果环境变量未设置
skip_integration = pytest.mark.skipif(
    not os.getenv("INTEGRATION_TESTS", "").lower() == "true",
    reason="Integration tests are disabled. Set INTEGRATION_TESTS=true to enable."
)

@pytest.fixture(scope="module")
def test_workflow():
    """测试用工作流数据"""
    return {
        "workflow": {
            "test_node": {
                "inputs": {
                    "text": "test input"
                },
                "class_type": "test_node_type"
            }
        },
        "client_id": "integration_test_client"
    }

@skip_integration
def test_full_workflow_execution(test_workflow):
    """测试完整的工作流执行流程"""
    # 1. 检查服务健康状态
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "healthy"

    # 2. 执行工作流
    execute_response = client.post("/api/workflow/execute", json=test_workflow)
    assert execute_response.status_code == 200
    prompt_id = execute_response.json().get("prompt_id")
    assert prompt_id is not None

    # 3. 检查工作流状态
    max_retries = 10
    retry_delay = 2
    for _ in range(max_retries):
        status_response = client.get(f"/api/workflow/status/{prompt_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        if status_data.get("status") in ["completed", "failed"]:
            break
            
        time.sleep(retry_delay)
    
    # 4. 检查队列状态
    queue_response = client.get("/api/workflow/queue")
    assert queue_response.status_code == 200

@skip_integration
def test_workflow_interrupt():
    """测试工作流中断功能"""
    # 1. 执行一个长时间运行的工作流
    long_workflow = {
        "workflow": {
            "long_running_node": {
                "inputs": {
                    "duration": 30
                },
                "class_type": "long_running_process"
            }
        },
        "client_id": "interrupt_test_client"
    }
    
    execute_response = client.post("/api/workflow/execute", json=long_workflow)
    assert execute_response.status_code == 200
    
    # 2. 等待一小段时间确保工作流开始执行
    time.sleep(2)
    
    # 3. 发送中断请求
    interrupt_response = client.post("/api/workflow/interrupt")
    assert interrupt_response.status_code == 200
    
    # 4. 验证工作流被中断
    queue_response = client.get("/api/workflow/queue")
    assert queue_response.status_code == 200

@skip_integration
def test_concurrent_workflows(test_workflow):
    """测试并发工作流执行"""
    # 同时发送多个工作流请求
    num_concurrent = 3
    responses = []
    
    for i in range(num_concurrent):
        workflow = test_workflow.copy()
        workflow["client_id"] = f"concurrent_test_client_{i}"
        response = client.post("/api/workflow/execute", json=workflow)
        assert response.status_code == 200
        responses.append(response.json())
    
    # 验证所有工作流都获得了不同的prompt_id
    prompt_ids = [r.get("prompt_id") for r in responses]
    assert len(set(prompt_ids)) == num_concurrent
    
    # 检查队列状态
    queue_response = client.get("/api/workflow/queue")
    assert queue_response.status_code == 200 