# __main__.py
import uvicorn
from src.client_agent_api import app  # 从模块导入FastAPI实例
from src.config.settings import API_CONFIG
import logging.config
import os

log_config_path = os.path.abspath("src/config/logging.conf")
logging.config.fileConfig(log_config_path, encoding='utf-8')
logger = logging.getLogger(__name__)

def run_api():
    """启动API服务的规范入口"""
    try:
        uvicorn.run(
            app,
            host=API_CONFIG['host'],
            port=API_CONFIG['port'],
            reload=False  # 生产环境应关闭
        )
    except Exception as e:
        logging.error(f"An error occurred while running the API: {e}", exc_info=True)

if __name__ == "__main__":
    # 支持两种启动方式：
    # 1. python -m your_project
    # 2. python __main__.py
    run_api()