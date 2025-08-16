from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from src.agent_executor import ChatAgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    InMemoryTaskStore,
)
import uvicorn

def main(host, port):
    # 说明智能体的技能
    skill = AgentSkill(
        id="555",
        name="chat agent",
        description="An Agent for Chat with user",
        tags=["chat"],
        examples=["给我讲个笑话", "今天大连天气怎么样？"],
    )

    # 构建AgentCard，也即智能体的名片
    coding_agent_card = AgentCard(
        name="Chat Agent",
        description="An Agent for Chat with user",
        url=f'http://localhost:{port}/',
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        version="1.0.0",
    )

    # 算法代码要被client调用，得用A2A的DefaultRequestHandler封装一下，让它可以应对来自client的请求，并自动执行CodingAgentExecutor中的对应函数
    request_handler = DefaultRequestHandler(
        agent_executor=ChatAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # 使用A2A SDK封装一个应用服务
    # Starlette框架简介
    # Starlette是一个轻量级的ASGI（异步服务器网关接口）框架/工具包，专为使用Python构建异步Web服务而设计。它既可以作为一个完整的框架使用，也可以作为ASGI工具包使用，其组件可以独立使用。
    server = A2AStarletteApplication(
        agent_card=coding_agent_card,
        http_handler=request_handler,
    )

    # 起服务
    uvicorn.run(server.build(), host=host, port=port)

if __name__ == "__main__":
    main('0.0.0.0', 10050)

