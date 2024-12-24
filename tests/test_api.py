import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import requests
from comfyui_service import app, Settings

client = TestClient(app)

@pytest.fixture
def mock_settings():
    return Settings()

@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"status": "success"}
    return mock

def test_health_check_healthy(mock_settings, mock_response):
    """测试健康检查接口 - 服务正常"""
    with patch('requests.get', return_value=mock_response):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "comfyui_service": "available"}

def test_health_check_unhealthy(mock_settings):
    """测试健康检查接口 - 服务异常"""
    with patch('requests.get', side_effect=Exception("Connection error")):
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json() == {"status": "unhealthy", "detail": "ComfyUI service unavailable"}

def test_execute_workflow_success(mock_settings, mock_response):
    """测试工作流执行 - 成功场景"""
    test_workflow = {
        "workflow": {"test": "data"},
        "client_id": "test_client"
    }
    mock_response.json.return_value = {"prompt_id": "test_id"}
    
    with patch('requests.post', return_value=mock_response):
        response = client.post("/api/workflow/execute", json=test_workflow)
        assert response.status_code == 200
        assert response.json() == {"prompt_id": "test_id"}

def test_execute_workflow_timeout(mock_settings):
    """测试工作流执行 - 超时场景"""
    test_workflow = {
        "workflow": {"test": "data"},
        "client_id": "test_client"
    }
    
    with patch('requests.post', side_effect=requests.Timeout):
        response = client.post("/api/workflow/execute", json=test_workflow)
        assert response.status_code == 504
        assert response.json() == {"detail": "ComfyUI service timeout"}

def test_get_workflow_status_success(mock_settings, mock_response):
    """测试获取工作流状态 - 成功场景"""
    mock_response.json.return_value = {"status": "completed"}
    
    with patch('requests.get', return_value=mock_response):
        response = client.get("/api/workflow/status/test_id")
        assert response.status_code == 200
        assert response.json() == {"status": "completed"}

def test_interrupt_workflow_success(mock_settings, mock_response):
    """测试中断工作流 - 成功场景"""
    with patch('requests.post', return_value=mock_response):
        response = client.post("/api/workflow/interrupt")
        assert response.status_code == 200
        assert response.json() == {"message": "Workflow interrupted successfully"}

def test_get_queue_status_success(mock_settings, mock_response):
    """测试获取队列状态 - 成功场景"""
    mock_response.json.return_value = {"queue_size": 0}
    
    with patch('requests.get', return_value=mock_response):
        response = client.get("/api/workflow/queue")
        assert response.status_code == 200
        assert response.json() == {"queue_size": 0}

def test_invalid_workflow_data():
    """测试无效的工作流数据"""
    invalid_workflow = {
        "invalid_key": "data"
    }
    response = client.post("/api/workflow/execute", json=invalid_workflow)
    assert response.status_code == 422  # Validation Error 