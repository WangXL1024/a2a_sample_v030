from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx
from src.config.settings import API_CONFIG
from fastapi.responses import StreamingResponse
from src.config.settings import REMOTE_AGENTS
import json
from src.agent_services import (
    AgentRegistry,
    AgentSelector,
    AgentQueryService
)
class QueryRequest(BaseModel):
    user_input: str
    session_id: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化服务
    http_client = httpx.AsyncClient(timeout=API_CONFIG['timeout'])
    registry = AgentRegistry(http_client)
    selector = AgentSelector()
    query_service = AgentQueryService(registry, selector)

    # 启动时注册所有Agent（仅一次）
    for agent_type, config in REMOTE_AGENTS.items():
        url = f"http://{config['host']}:{config['port']}"
        await registry.register_agent(url)
    
    # 注入到app state
    app.state.services = {
        'http_client': http_client,
        'registry': registry,
        'query_service': query_service,
        'selector': selector
    }
    
    yield
    
    # 清理资源
    await http_client.aclose()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/stream-query")
async def handle_stream_query(request: QueryRequest):
    services = app.state.services
    
    async def generate():
        async for content in services['query_service'].handle_stream_query(request.user_input,request.session_id):
            # 将字典转换为JSON字符串
            json_data = json.dumps(content)
            # 按照SSE格式返回，每个事件以两个换行符结束
            yield f"data: {json_data}\n\n"     

    return StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )