import logging
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from src.agent import AutoRecommendAgent
from src.agent_executor import AutoRecommendAgentExecutor
import uvicorn

logging.basicConfig(level=logging.INFO)
# 禁用httpx、httpcore和asyncio的噪音日志
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main(host, port):
    """Start Automobile Recommendation Agent Server.
    """
    logger.info("Start Automobile Recommendation Agent Server.")

    skill = AgentSkill(
        id='222',
        name='Automobile Recommendation',
        description='Query relevant data from the database for automobile recommendation to user',
        tags=['Automobile Recommendation', 'Auto Recommend'],
        examples=['Recommend a car for me', 'What is the best car for my budget?'],
    )
    agent_card = AgentCard(
        name='Automobile Recommendation Agent',
        description='Query relevant data from the database for automobile recommendation to user',
        url=f'http://localhost:{port}/',
        version='1.0.0',
        defaultInputModes=AutoRecommendAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=AutoRecommendAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=AutoRecommendAgentExecutor(),
        task_store=InMemoryTaskStore()
    )
    server = A2AStarletteApplication(
        agent_card=agent_card, 
        http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)

if __name__ == '__main__':
    main('0.0.0.0', 10020)
