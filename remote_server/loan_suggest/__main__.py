from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from src.agent import LoanSuggestAgent
from src.agent_executor import LoanSuggestAgentExecutor
import uvicorn


def main(host, port):
    """Start the Loan Suggest Agent server.
    """
    capabilities = AgentCapabilities(
        streaming=True)
    skill = AgentSkill(
        id='333',
        name='loan suggest',
        description='Give the loan scheme suggestion to user',
        tags=['loan scheme suggestion', 'loan scheme', 'loan suggestion', 'loan suggest'],
        examples=['What is the best loan scheme for me?', 'Suggest a loan scheme based on my requirements'],
    )
    agent_card = AgentCard(
        name='Loan Scheme Suggestion Agent',
        description='Give the loan scheme suggestion to user',
        url=f'http://localhost:{port}/',
        version='1.0.0',
        defaultInputModes=LoanSuggestAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=LoanSuggestAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=LoanSuggestAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=agent_card, 
        http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)

if __name__ == '__main__':
    main('0.0.0.0', 10030)
