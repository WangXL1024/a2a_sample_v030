import logging
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import  InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from src.agent import LoanPreExaminationAgent
from src.agent_executor import LoanPreExaminationAgentExecutor
import uvicorn

def main(host, port):
    """Start the Loan Pre-examination Agent server.
    """
    # logger.info("Start the Loan Pre-examination Agent server.")
    capabilities = AgentCapabilities(
        streaming=True)
    skill = AgentSkill(
        id='444',
        name='loan pre-examination',
        description='Based on the user basic information, conduct a loan pre-examination',
        tags=['loan pre-examination', 'pre-examination'],
        examples=['What is the loan pre-examination result for me?'],
    )
    agent_card = AgentCard(
        name='Loan Pre-examination Agent',
        description='Conduct loan pre-approval for users',
        url=f'http://localhost:{port}/',
        version='1.0.0',
        defaultInputModes=LoanPreExaminationAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=LoanPreExaminationAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=LoanPreExaminationAgentExecutor(),
        task_store=InMemoryTaskStore()
    )
    server = A2AStarletteApplication(
        agent_card=agent_card, 
        http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)

if __name__ == '__main__':
    main('0.0.0.0', 10040)
