from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from src.agent_executor import ChatAgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    InMemoryTaskStore,
)
import uvicorn
from pydantic import ValidationError
import logging.config
import os

log_config_path = os.path.abspath("src/config/logging.conf")
logging.config.fileConfig(log_config_path, encoding='utf-8')
logger = logging.getLogger(__name__)

def main(host, port):
    logger.info(f"Starting Chat Agent service on host: {host}, port: {port}")

    try:
        # 创建AgentSkill
        skill = AgentSkill(
            id="555",
            name="chat agent",
            description="An Agent for Chat with user",
            tags=["chat"],
            examples=["给我讲个笑话", "今天大连天气怎么样？"],
        )
        logger.info("AgentSkill created")

        # 构建AgentCard，也即智能体的名片
        agent_card = AgentCard(
            name="Chat Agent",
            description="An Agent for Chat with user",
            url=f'http://localhost:{port}/',
            capabilities=AgentCapabilities(streaming=True),
            skills=[skill],
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            version="1.0.0",
        )
        logger.info("AgentCard created")
    except ValidationError as ve:
        logger.error(f"Invalid configuration: {ve}")
        return
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return

    try:
        # 算法代码要被client调用，得用A2A的DefaultRequestHandler封装一下，让它可以应对来自client的请求，并自动执行CodingAgentExecutor中的对应函数
        request_handler = DefaultRequestHandler(
            agent_executor=ChatAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        logger.info("DefaultRequestHandler created")
    except (TypeError, ValueError) as e:
        logger.critical(f"Configuration error in RequestHandler: {e}")
        return
    except Exception as e:
        logger.exception(f"Unexpected error creating RequestHandler: {e}")
        return

    # 使用A2A SDK封装一个应用服务
    # Starlette框架简介
    # Starlette是一个轻量级的ASGI（异步服务器网关接口）框架/工具包，专为使用Python构建异步Web服务而设计。它既可以作为一个完整的框架使用，也可以作为ASGI工具包使用，其组件可以独立使用。
    # 创建Starlette应用
    try:
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
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

if __name__ == "__main__":
    main('0.0.0.0', 10050)

