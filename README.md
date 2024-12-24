# ComfyUI API Service

这是一个封装了ComfyUI服务的FastAPI后端服务，专门用于与部署在腾讯云HAI服务上的ComfyUI进行交互。

## 功能特性

- 工作流执行API
- 状态查询API
- 队列管理
- 任务中断
- 健康检查

## 安装步骤

1. 克隆项目到本地
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 复制环境变量配置：
   ```bash
   cp .env.example .env
   ```
4. 修改.env文件中的配置，特别是`COMFYUI_BASE_URL`要设置为你的HAI服务地址

## 启动服务

```bash
python comfyui_service.py
```

或者使用uvicorn：
```bash
uvicorn comfyui_service:app --host 0.0.0.0 --port 8000 --reload
```

## API文档

启动服务后，访问 http://localhost:8000/docs 查看完整的API文档。

### 主要接口

- POST /api/workflow/execute - 执行工作流
- GET /api/workflow/status/{prompt_id} - 获取工作流状态
- POST /api/workflow/interrupt - 中断当前工作流
- GET /api/workflow/queue - 获取队列状态
- GET /health - 健康检查

## 注意事项

1. 确保ComfyUI服务在腾讯云HAI上正确部署并可���问
2. 正确配置COMFYUI_BASE_URL环境变量
3. 注意处理跨域访问问题
4. 建议在生产环境中配置适当的安全措施 