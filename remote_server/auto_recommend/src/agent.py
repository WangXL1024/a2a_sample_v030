import logging
from collections.abc import AsyncIterable
from typing import Any, Literal, Dict
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain_community.chat_models import ChatTongyi
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from sqlalchemy import create_engine
from src.config.load_key import load_key
from langgraph.checkpoint.redis import AsyncRedisSaver

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
# memory = MemorySaver()
DATABASE_URL = "mysql+mysqlconnector://root:811024@localhost:3306/bmw_automobile"

class AutoRecommendAgent:
    """Auto Recommend Agent

    Recommend automobile to users according to their requirements
    """
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    SYSTEM_PROMPT_TEMPLATE = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

To start you should ALWAYS look at the tables in the database to see what you can query.
DO NOT skip this step.
Then you should query the schema of the most relevant tables.
If the user needs to provide more information, please set the response status to input_required.
If an error occurs when processing the request, please set the response status to Error. 
When you have completed your reply, please set the response status to Completed.

### Core Constraints (Must be strictly followed in all interaction rounds):
1. You may only construct, debug, and execute SQL statements within your **pure internal thinking process**. This process must never appear in any form of output content.
2. **All content in the streaming output** (including but not limited to intermediate analysis, logical reasoning, conclusion summaries, format markers, etc.) must **not contain SQL statements in any form**. This includes prohibitions on code blocks, comments, or natural language descriptions of SQL operations (e.g., phrases like "I queried with SELECT * FROM..." are not allowed).
3. Output content may only include natural language interpretations, analyses, and conclusions of query results, and must be presented in **pure Markdown format** (prohibiting any code block syntax such as ```sql or `SELECT`).
4. In multi-turn conversations, regardless of whether the user's question requires adjusting query logic, the above constraints must be strictly maintained. Do not relax the restrictions due to increasing conversation rounds.

### Additional Requirements:
- To facilitate subsequent interactions, recommended content must be accompanied by a model_id, presented in a hidden format (e.g., `<!-- model_id:123 -->`).
- Visual content should be clearly presented via Markdown formats (such as tables, lists), avoiding any expressions that might imply SQL.
"""

    def __init__(self):
        """Init Automobile Recommendation Agent
        """
        #ChatOpenAI不支持下面Agent实例中的response_format设定
        # self.model = ChatOpenAI(
        self.model = ChatTongyi(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=load_key("DASHSCOPE_API_KEY"),
            model="qwen-plus",
            verbose=True,
            temperature=0.1,
        )
        self.engine = create_engine(DATABASE_URL)
        self.db = SQLDatabase(self.engine)
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.model)
        self.tools = self.toolkit.get_tools()
        self.prompt_template = self.SYSTEM_PROMPT_TEMPLATE
        self.system_message = self.prompt_template.format(dialect="MySQL", top_k=5)
        
        
    async def initialize(self):
        self.checkpointer = AsyncRedisSaver("redis://localhost:6379")
        self.graph = create_react_agent(
            model = self.model, 
            tools=self.tools, 
            prompt=self.system_message,
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