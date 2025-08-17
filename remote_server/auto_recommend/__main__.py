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
from pydantic import ValidationError
import logging.config
import os

log_config_path = os.path.abspath("src/config/logging.conf")
logging.config.fileConfig(log_config_path, encoding='utf-8')
logger = logging.getLogger(__name__)


def main(host, port):
    logger.info(f"Starting Automobile Recommendation Agent service on host: {host}, port: {port}")

    try:
        # 创建AgentSkill
        skill = AgentSkill(
            id='222',
            name='Automobile Recommendation',
            description='Query relevant data from the database for automobile recommendation to user',
            tags=['Automobile Recommendation', 'Auto Recommend'],
            examples=['Recommend a car for me', 'What is the best car for my budget?'],
        )
        logger.info("AgentSkill created")
    
        # 创建AgentCard
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
        logger.info("AgentCard created")
    except ValidationError as ve:
        logger.error(f"Invalid configuration: {ve}")
        return
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return
    
    # 创建请求处理器 - 区分配置错误和未知错误
    try:
        request_handler = DefaultRequestHandler(
            agent_executor=AutoRecommendAgentExecutor(),
            task_store=InMemoryTaskStore()
        )
        logger.info("DefaultRequestHandler created")
    except (TypeError, ValueError) as e:
        logger.critical(f"Configuration error in RequestHandler: {e}")
        return
    except Exception as e:
        logger.exception(f"Unexpected error creating RequestHandler: {e}")
        return
    
    # 创建Starlette应用
    try:
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )
        logger.info("A2AStarletteApplication created")
    except Exception as e:
        logger.exception(f"Failed to create A2AStarletteApplication: {e}")
        return
    
    # 启动服务 - 添加端口冲突处理
    try:
        logger.info(f"Service starting at http://{host}:{port}")
        uvicorn.run(server.build(), host=host, port=port)
    except OSError as e:
        if "address in use" in str(e):
            logger.error(f"Port {port} already in use. Please choose another port.")
        else:
            logger.exception(f"Network error: {e}")
    except Exception as e:
        logger.exception(f"Service startup failed: {e}")
    finally:
        # 资源清理 - 实际应用中根据组件需要添加
        logger.info("Performing service shutdown cleanup...")
        
        # 示例：如果使用需要关闭的连接
        # if database_connection:
        #     database_connection.close()
        
        # 对于InMemoryTaskStore，通常不需要额外清理
        logger.info("Service shutdown complete")

if __name__ == '__main__':
    main('0.0.0.0', 10020)
