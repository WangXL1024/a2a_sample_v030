from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import httpx
from src.client_agent import ClientAgent
from src.config.settings import API_CONFIG
from fastapi.responses import StreamingResponse
import json
import os
import logging.config

log_config_path = os.path.abspath("src/config/logging.conf")
logging.config.fileConfig(log_config_path, encoding='utf-8')
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    user_input: str
    session_id: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化服务
    http_client = httpx.AsyncClient(timeout=API_CONFIG['timeout'])
    
    # 注入到app state
    app.state.services = {
        'http_client': http_client
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
    logger.info(f"Handling stream query for user_input: {request.user_input}, session_id: {request.session_id}")
    client_agent = ClientAgent()
    
    async def generate():
        try:
            async for content in client_agent.invoke(
                base_url="http://localhost:10010",
                user_input=request.user_input,
                session_id=request.session_id
            ):
                # 将字典转换为JSON字符串
                json_data = json.dumps(content)
                # 按照SSE格式返回，每个事件以两个换行符结束
                yield f"data: {json_data}\n\n"         
        except Exception as e:
            logger.error(f"Error during stream query: {str(e)}")
            yield f"data: {{'error': '{str(e)}'}}\n\n"
    return StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )