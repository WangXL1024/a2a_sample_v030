from typing import AsyncIterable, Dict, Any
from langgraph.prebuilt import create_react_agent
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import AIMessageChunk
from src.config.load_key import load_key
from langgraph.checkpoint.redis import AsyncRedisSaver
from langchain_core.runnables import RunnableConfig
import logging.config
import os
log_config_path = os.path.abspath("src/config/logging.conf")

logging.config.fileConfig(log_config_path,encoding='utf-8')
logger = logging.getLogger("agent")

logger.info('使用配置文件的日志')

# server是专家智能体，基本不用改变智能体原有的逻辑
class CodingAgent:
    SYSTEM_PROMPT = "你是一个代码助手，根据用户的输入，生成对应的代码。注意你只能写代码，遇到不是代码的问题需要你反问用户，让用户明确需求"

    def __init__(self) -> None:
        self.model = ChatTongyi(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=load_key("DASHSCOPE_API_KEY"),
            model="qwen-plus",
        )
    
    # Redis checkpointer 需要单独初始化
    async def initialize(self):
        self.checkpointer = AsyncRedisSaver("redis://localhost:6379")
        self.graph = create_react_agent(
            model = self.model, 
            tools=[], 
            prompt=self.SYSTEM_PROMPT,
            checkpointer=self.checkpointer
        )
    async def stream(
        self, messages ,session_id
    ) -> AsyncIterable[Dict[str, Any]]: 
        config: RunnableConfig = {'configurable': {'thread_id': session_id}}
        async for item in self.graph.astream(input={"messages": messages},config=config, stream_mode='messages'):
                if isinstance(item[0],AIMessageChunk):
                    yield {
                        'is_final_answer': False,
                        'content': item[0].content,
                    }
        # 循环结束后，发送输出结束的标志
        yield {
            'is_final_answer': True,  # 任务已完成
            'content': '',  # 可以为空或适当的结束信息
        }
