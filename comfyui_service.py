from fastapi import FastAPI, HTTPException, UploadFile, File, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import requests
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging
from functools import lru_cache

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 配置类
class Settings:
    def __init__(self):
        self.COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", "http://your-hai-service-url")
        self.PORT = int(os.getenv("PORT", "8000"))
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

app = FastAPI(
    title="ComfyUI API Service",
    description="腾讯云HAI ComfyUI服务的API封装",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WorkflowRequest(BaseModel):
    workflow: Dict[str, Any]
    client_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "workflow": {"your_workflow_data": "here"},
                "client_id": "optional_client_id"
            }
        }

async def check_comfyui_service():
    """检查ComfyUI服务是否可用"""
    try:
        response = requests.get(
            f"{settings.COMFYUI_BASE_URL}/queue",
            timeout=settings.REQUEST_TIMEOUT
        )
        return response.status_code == 200
    except:
        return False

@app.get("/health")
async def health_check():
    """健康检查接口"""
    comfyui_available = await check_comfyui_service()
    if not comfyui_available:
        return Response(
            content=json.dumps({"status": "unhealthy", "detail": "ComfyUI service unavailable"}),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )
    return {"status": "healthy", "comfyui_service": "available"}

@app.post("/api/workflow/execute")
async def execute_workflow(request: WorkflowRequest):
    """执行工作流"""
    try:
        logger.info(f"Executing workflow with client_id: {request.client_id}")
        url = f"{settings.COMFYUI_BASE_URL}/prompt"
        
        data = {
            "prompt": request.workflow,
            "client_id": request.client_id or "default_client"
        }
        
        response = requests.post(
            url,
            json=data,
            timeout=settings.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Workflow execution successful: {result.get('prompt_id', 'No ID')}")
        return result
    except requests.Timeout:
        logger.error("Workflow execution timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="ComfyUI service timeout"
        )
    except requests.RequestException as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ComfyUI service error: {str(e)}"
        )

@app.get("/api/workflow/status/{prompt_id}")
async def get_workflow_status(prompt_id: str):
    """获取工作流状态"""
    try:
        url = f"{settings.COMFYUI_BASE_URL}/history/{prompt_id}"
        response = requests.get(url, timeout=settings.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Status check timeout"
        )
    except requests.RequestException as e:
        logger.error(f"Failed to get workflow status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )

@app.post("/api/workflow/interrupt")
async def interrupt_workflow():
    """中断当前工作流"""
    try:
        url = f"{settings.COMFYUI_BASE_URL}/interrupt"
        response = requests.post(url, timeout=settings.REQUEST_TIMEOUT)
        response.raise_for_status()
        return {"message": "Workflow interrupted successfully"}
    except requests.RequestException as e:
        logger.error(f"Failed to interrupt workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to interrupt workflow: {str(e)}"
        )

@app.get("/api/workflow/queue")
async def get_queue_status():
    """获取队列状态"""
    try:
        url = f"{settings.COMFYUI_BASE_URL}/queue"
        response = requests.get(url, timeout=settings.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue status: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    ) 