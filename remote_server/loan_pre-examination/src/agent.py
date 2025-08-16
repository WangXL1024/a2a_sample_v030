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

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

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


class LoanPreExaminationAgent:
    """An agent conduct a loan pre-examination based on LangGraph.
    Based on the basic information provided by the user, conduct a loan pre-examination
    """
    
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    SYSTEM_INSTRUCTION = (
        """
        You act as a loan pre-examiner for BMW Auto Finance, 
        responsible for conducting loan pre-examination based on the information provided by the user. 
        The user must provide three pieces of information: user name, ID card number, and phone number, 
        none of which can be missing. After obtaining the above information, 
        and then obtain the user's authorization application for get credit information. After obtaining the authorization (the user enters "accept")
        please call the "get_credit_info" tool method for acquiring the user's credit information, 
        conduct the examination based on the obtained user's credit information, 
        and then judge whether the user is eligible for a loan.
        It should be specifically clarified that the standard for a user's credit status being intact is that there are no bad records in the credit report, 
        including but not limited to such poor performance as overdue credit card repayments, overdue loan repayments, etc. 
        Finally, you need to feedback the pre-examination result (i.e., whether it is passed) to the user, 
        and must strictly follow the following principle: the loan pre-examination can only be passed if the user's credit report fully meets the above "intact" standard
        Before feeding back the pre-examination result to the user, 
        you must call the "create_examination_result" tool method 
        and pass the following information as parameters to store the pre-examination result in MongoDB: ID number (id_number), phone number (phone_number), and pre-examination result (result, with a value of either "passed" or "unpassed").
        If the user needs to provide more information, please set the response status to input_required.
        If an error occurs when processing the request, please set the response status to Error. 
        When you have completed your reply, please set the response status to Completed.
        """
    )

    def __init__(self):
        """Init loan pre-examination Agent
        """
        #ChatOpenAI不支持下面Agent实例中的response_format设定
        # self.model = ChatOpenAI(
        self.model = ChatTongyi(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=load_key("DASHSCOPE_API_KEY"),
            model="qwen-plus",
        )

    async def initialize(self):
        self.checkpointer = AsyncRedisSaver("redis://localhost:6379")
        self.tools = await mcp_client.get_tools()
        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=self.checkpointer,
            prompt=self.SYSTEM_INSTRUCTION,
            # response_format=ResponseFormat,
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
