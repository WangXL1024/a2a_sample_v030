import logging
from collections.abc import AsyncIterable
from typing import Any, Dict, Literal
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_community.chat_models import ChatTongyi
from src.config.load_key import load_key
from langgraph.checkpoint.redis import AsyncRedisSaver
import os
import logging.config

log_config_path = os.path.abspath("src/config/logging.conf")
logging.config.fileConfig(log_config_path,encoding='utf-8')
logger = logging.getLogger(__name__)

mcp_client = MultiServerMCPClient(
    {
        "auto_finance_mcp": {
            # "url": "http://host.docker.internal:8000/mcp",
            "url": "http://localhost:8000/mcp",
            "transport": "streamable_http",
        }
    }
)

# class ResponseFormat(BaseModel):
#     """向用户返回响应的标准格式。"""

#     status: Literal['input_required', 'completed', 'error'] = 'input_required'
#     message: str = Field(description="Detailed response message. For the input_required status, it is necessary to specify what information is required. For the error status, it is necessary to explain what the problem is.")


class LoanSuggestAgent:
    """An agent providing auto loan scheme suggestion based on LangGraph.
    Based on the basic information provided by the user, reasonable suggestions for the user's auto loan are made
    """

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    SYSTEM_INSTRUCTION = (
        """
        You are an expert in BMW automotive financial loan schemes. 
        Based on all communication with the user (including user input and contextual information), 
        accurately extract the vehicle model ID (model_id). After extraction, 
        call the `get_loan_scheme_from_rag` tool method to obtain the corresponding loan scheme, 
        and present clear and reasonable scheme suggestions to the user in Markdown format, 
        ensuring that the information is accurate and easy to understand.
        It should be noted that the model_id must be presented in a hidden form (for example, using the Markdown format `<!-- here replace the model_id -->`).
        If the user needs to provide more information, please set the response status to input_required.
        If an error occurs when processing the request, please set the response status to Error. 
        When you have completed your reply, please set the response status to Completed.
        """
    )

    def __init__(self):
        logger.info("Initializing auto loan scheme suggestion Agent")
        #ChatOpenAI不支持下面Agent实例中的response_format设定
        try:
            # self.model = ChatOpenAI(
            self.model = ChatTongyi(
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                api_key=load_key("DASHSCOPE_API_KEY"),
                model="qwen-plus",
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatTongyi model: {e}")
            raise

    async def initialize(self):
        logger.info("Initializing Redis checkpointer for Agent")
        try:
            self.checkpointer = AsyncRedisSaver("redis://localhost:6379")
            logger.info("Redis checkpointer initialized")
            self.tools = await mcp_client.get_tools()
            self.graph = create_react_agent(
                self.model,
                tools=self.tools,
                checkpointer=self.checkpointer,
                prompt=self.SYSTEM_INSTRUCTION,
                # response_format=ResponseFormat,               
            )
            logger.info("React agent created with Redis checkpointer")
        except Exception as e:
            logger.error(f"Failed to initialize Redis checkpointer or create React agent: {e}")
            raise

    async def stream(
        self, messages, session_id
    ) -> AsyncIterable[Dict[str, Any]]:
        logger.info(f"Starting stream processing for session ID: {session_id}")
        config: RunnableConfig = {'configurable': {'thread_id': session_id}}
        try:
            async for item in self.graph.astream(input={"messages": messages}, config=config, stream_mode='messages'):
                if isinstance(item[0], AIMessageChunk):
                    logger.debug(f"Received message chunk: {item[0].content}")
                    yield {
                        'is_final_answer': False,
                        'content': item[0].content,
                    }
        except Exception as e:
            logger.error(f"Error during stream processing for session ID {session_id}: {e}")
            raise
        logger.info(f"Stream processing completed for session ID: {session_id}")
        # 循环结束后，发送输出结束的标志
        yield {
            'is_final_answer': True,  # 任务已完成
            'content': '',  # 可以为空或适当的结束信息
        }


    